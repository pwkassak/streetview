#!/usr/bin/env python3
"""
Progressive scaling test to find performance limits.
Tests increasingly larger areas until timeout or failure.
"""

import time
import sys
import signal
from map_loader import MapLoader
from cpp_solver import CPPSolver

# Timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

def test_with_timeout(func, timeout_seconds=30):
    """Run a function with a timeout."""
    # Set the timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = func()
        signal.alarm(0)  # Cancel the alarm
        return result
    except TimeoutException:
        signal.alarm(0)
        raise
    except Exception as e:
        signal.alarm(0)
        raise


def test_scaling():
    """Test with progressively larger areas to find limits."""
    
    print("="*60)
    print("PROGRESSIVE SCALING TEST")
    print("Finding performance limits for route planning")
    print("="*60)
    
    # Center point in Downtown Berkeley (Shattuck & Center St)
    center_lat = 37.8706
    center_lon = -122.2686
    
    # Test with increasing radii (starting larger to ensure we get streets)
    test_configs = [
        {"name": "200m radius", "size": 0.002, "timeout": 10},
        {"name": "300m radius", "size": 0.003, "timeout": 15},
        {"name": "400m radius", "size": 0.004, "timeout": 20},
        {"name": "500m radius", "size": 0.005, "timeout": 30},
        {"name": "750m radius", "size": 0.0075, "timeout": 45},
        {"name": "1km radius", "size": 0.01, "timeout": 60},
        {"name": "1.5km radius", "size": 0.015, "timeout": 90},
        {"name": "2km radius", "size": 0.02, "timeout": 120},
    ]
    
    loader = MapLoader('drive')
    results = []
    last_successful = None
    
    for config in test_configs:
        print(f"\n--- Testing {config['name']} ---")
        
        # Calculate bounds
        north = center_lat + config['size']
        south = center_lat - config['size']
        east = center_lon + config['size']
        west = center_lon - config['size']
        
        # Estimate area
        km_size = config['size'] * 111
        area_km2 = (km_size * 2) ** 2
        print(f"Approximate area: {area_km2:.3f} km²")
        print(f"Timeout: {config['timeout']}s")
        
        result = {
            'name': config['name'],
            'area_km2': area_km2,
            'timeout': config['timeout']
        }
        
        try:
            # Test loading
            print("Loading graph...", end=' ')
            load_start = time.time()
            
            def load_graph():
                return loader.load_by_bbox(north, south, east, west)
            
            graph = test_with_timeout(load_graph, config['timeout'])
            load_time = time.time() - load_start
            
            print(f"✓ ({load_time:.2f}s)")
            print(f"  Nodes: {graph.number_of_nodes()}")
            print(f"  Edges: {graph.number_of_edges()}")
            
            result['load_time'] = load_time
            result['nodes'] = graph.number_of_nodes()
            result['edges'] = graph.number_of_edges()
            
            # Test solving
            print("Solving CPP...", end=' ')
            solve_start = time.time()
            
            def solve_cpp():
                solver = CPPSolver(graph)
                return solver.solve(), solver
            
            route, solver = test_with_timeout(solve_cpp, int(config['timeout'] - load_time))
            solve_time = time.time() - solve_start
            
            print(f"✓ ({solve_time:.2f}s)")
            
            stats = solver.get_route_stats()
            print(f"  Route edges: {len(route)}")
            print(f"  Distance: {stats.get('total_distance_km', 0):.2f} km")
            
            result['solve_time'] = solve_time
            result['total_time'] = load_time + solve_time
            result['route_edges'] = len(route)
            result['distance_km'] = stats.get('total_distance_km', 0)
            result['success'] = True
            
            last_successful = result
            
        except TimeoutException:
            print(f"✗ TIMEOUT after {config['timeout']}s")
            result['success'] = False
            result['reason'] = 'timeout'
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            result['success'] = False
            result['reason'] = str(e)
        
        results.append(result)
        
        # Stop if we hit failure
        if not result['success']:
            print(f"\nStopping at {config['name']} due to failure")
            break
    
    # Analysis
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    print(f"{'Name':<15} {'Area(km²)':<10} {'Load(s)':<8} {'Solve(s)':<8} {'Total(s)':<8} {'Edges':<8} {'Status'}")
    print("-" * 75)
    
    for r in results:
        if r['success']:
            print(f"{r['name']:<15} "
                  f"{r['area_km2']:<10.3f} "
                  f"{r['load_time']:<8.2f} "
                  f"{r['solve_time']:<8.2f} "
                  f"{r['total_time']:<8.2f} "
                  f"{r['edges']:<8} "
                  f"✓")
        else:
            print(f"{r['name']:<15} "
                  f"{r['area_km2']:<10.3f} "
                  f"{'---':<8} "
                  f"{'---':<8} "
                  f"{'---':<8} "
                  f"{'---':<8} "
                  f"✗ ({r['reason']})")
    
    # Find limits
    print("\n" + "="*60)
    print("PERFORMANCE LIMITS")
    print("="*60)
    
    successful = [r for r in results if r['success']]
    
    if successful:
        # Find maximum successful size
        max_success = max(successful, key=lambda x: x['area_km2'])
        print(f"✓ Maximum successful area: {max_success['area_km2']:.3f} km²")
        print(f"  - {max_success['edges']} edges")
        print(f"  - {max_success['total_time']:.1f}s total time")
        
        # Check if we're CPU bound or network bound
        avg_load_ratio = sum(r['load_time']/r['total_time'] for r in successful) / len(successful)
        avg_solve_ratio = sum(r['solve_time']/r['total_time'] for r in successful) / len(successful)
        
        print(f"\nTime distribution (average):")
        print(f"  Loading: {avg_load_ratio*100:.0f}%")
        print(f"  Solving: {avg_solve_ratio*100:.0f}%")
        
        if avg_solve_ratio > 0.7:
            print("\n⚠️ CPU-bound: Solver is the bottleneck")
            print("  Consider:")
            print("  - Using approximation algorithms")
            print("  - Limiting area size")
            print("  - Adding progress indicators")
        elif avg_load_ratio > 0.7:
            print("\n⚠️ Network-bound: OSM loading is the bottleneck")
            print("  Consider:")
            print("  - Better caching strategy")
            print("  - Pre-loading common areas")
            print("  - Showing loading progress")
        
        # Recommend safe limits
        print("\n" + "="*60)
        print("RECOMMENDED LIMITS")
        print("="*60)
        
        # Use 50% of max successful as safe limit
        safe_edges = max_success['edges'] // 2
        safe_area = max_success['area_km2'] / 2
        
        print(f"For reliable performance (< 30s):")
        print(f"  - Limit area to {safe_area:.3f} km²")
        print(f"  - Approximately {safe_edges} edges")
        
        # Find the test that matches this
        for r in successful:
            if r['edges'] <= safe_edges:
                print(f"  - Example: {r['name']} completed in {r['total_time']:.1f}s")
                break
    
    else:
        print("✗ No successful tests!")
        print("  Check network connection and OSM availability")
    
    return results


if __name__ == "__main__":
    try:
        results = test_scaling()
        
        # Return success if at least one test passed
        if any(r['success'] for r in results):
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)