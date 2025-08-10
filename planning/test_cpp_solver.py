#!/usr/bin/env python3
"""
Test CPP solver performance in isolation.
Uses pre-loaded graphs to test solver without OSM delays.
"""

import time
import sys
from map_loader import MapLoader
from cpp_solver import CPPSolver

def test_cpp_solver():
    """Test CPP solver with progressively larger graphs."""
    
    print("="*60)
    print("CPP SOLVER PERFORMANCE TEST")
    print("="*60)
    
    # Test areas with known good coordinates
    test_areas = [
        {
            "name": "Small (2-3 blocks)",
            "north": 37.8716,
            "south": 37.8696,
            "east": -122.2676,
            "west": -122.2696,
        },
        {
            "name": "Medium (10-15 blocks)",
            "north": 37.8687,
            "south": 37.8637,
            "east": -122.2573,
            "west": -122.2623,
        },
        {
            "name": "Large (50+ blocks)",
            "north": 37.8749,
            "south": 37.8669,
            "east": -122.2547,
            "west": -122.2627,
        }
    ]
    
    loader = MapLoader('drive')
    results = []
    
    for area in test_areas:
        print(f"\n--- Testing {area['name']} ---")
        
        # First load the graph
        print("Loading graph from OSM...")
        try:
            load_start = time.time()
            graph = loader.load_by_bbox(
                area['north'], 
                area['south'], 
                area['east'], 
                area['west']
            )
            load_time = time.time() - load_start
            print(f"  Graph loaded in {load_time:.2f}s")
            print(f"  Nodes: {graph.number_of_nodes()}")
            print(f"  Edges: {graph.number_of_edges()}")
            
        except Exception as e:
            print(f"  ✗ Failed to load graph: {e}")
            results.append({
                'name': area['name'],
                'success': False,
                'error': f"Load failed: {e}"
            })
            continue
        
        # Now test the solver
        print("Running CPP solver...")
        try:
            solver = CPPSolver(graph)
            
            solve_start = time.time()
            route = solver.solve()
            solve_time = time.time() - solve_start
            
            # Get statistics
            stats = solver.get_route_stats()
            
            print(f"  ✓ Solver completed in {solve_time:.2f}s")
            print(f"  Route edges: {len(route)}")
            print(f"  Original edges: {graph.number_of_edges()}")
            print(f"  Repeated edges: {stats.get('repeated_edges', 0)}")
            print(f"  Total distance: {stats.get('total_distance_km', 0):.2f} km")
            print(f"  Edge coverage: {stats.get('edge_coverage', 0):.1f}%")
            
            results.append({
                'name': area['name'],
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges(),
                'load_time': load_time,
                'solve_time': solve_time,
                'route_edges': len(route),
                'repeated_edges': stats.get('repeated_edges', 0),
                'distance_km': stats.get('total_distance_km', 0),
                'success': True
            })
            
        except Exception as e:
            print(f"  ✗ Solver failed: {e}")
            results.append({
                'name': area['name'],
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges(),
                'load_time': load_time,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    print(f"{'Area':<20} {'Load(s)':<8} {'Solve(s)':<8} {'Edges':<8} {'Route':<8} {'Status':<10}")
    print("-" * 70)
    
    for result in results:
        if result['success']:
            print(f"{result['name']:<20} "
                  f"{result['load_time']:<8.2f} "
                  f"{result['solve_time']:<8.2f} "
                  f"{result['edges']:<8} "
                  f"{result['route_edges']:<8} "
                  f"✓ OK")
        else:
            print(f"{result['name']:<20} "
                  f"{result.get('load_time', 0):<8.2f} "
                  f"{'N/A':<8} "
                  f"{result.get('edges', 'N/A'):<8} "
                  f"{'N/A':<8} "
                  f"✗ FAILED")
    
    # Performance analysis
    print("\n" + "="*60)
    print("PERFORMANCE ANALYSIS")
    print("="*60)
    
    successful = [r for r in results if r['success']]
    if successful:
        avg_load = sum(r['load_time'] for r in successful) / len(successful)
        avg_solve = sum(r['solve_time'] for r in successful) / len(successful)
        
        print(f"Average load time: {avg_load:.2f}s")
        print(f"Average solve time: {avg_solve:.2f}s")
        
        # Check scaling
        if len(successful) > 1:
            print("\nScaling analysis:")
            for i in range(1, len(successful)):
                prev = successful[i-1]
                curr = successful[i]
                
                edge_ratio = curr['edges'] / prev['edges'] if prev['edges'] > 0 else float('inf')
                solve_ratio = curr['solve_time'] / prev['solve_time'] if prev['solve_time'] > 0 else float('inf')
                
                print(f"\n{prev['name']} → {curr['name']}:")
                print(f"  Edges: {prev['edges']} → {curr['edges']} ({edge_ratio:.1f}x)")
                print(f"  Solve time: {prev['solve_time']:.2f}s → {curr['solve_time']:.2f}s ({solve_ratio:.1f}x)")
                
                # Check if solve time scales worse than O(n^3) 
                # (CPP is polynomial but can be expensive)
                if solve_ratio > edge_ratio ** 3:
                    print(f"  ⚠️ WARNING: Solve time scaling poorly (>{edge_ratio**3:.1f}x expected)")
                elif solve_ratio > edge_ratio ** 2:
                    print(f"  ⚠️ Note: Solve time scaling faster than quadratic")
                else:
                    print(f"  ✓ Reasonable scaling")
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if successful:
        max_edges = max(r['edges'] for r in successful)
        max_solve_time = max(r['solve_time'] for r in successful)
        
        if max_solve_time < 5:
            print("✓ Solver performance is good for tested areas")
            if max_edges < 500:
                print("  Consider testing larger areas")
        elif max_solve_time < 30:
            print("⚠️ Solver is slow but usable for small/medium areas")
            print(f"  Maximum tested: {max_edges} edges in {max_solve_time:.1f}s")
        else:
            print("✗ Solver is too slow for practical use")
            print(f"  {max_edges} edges took {max_solve_time:.1f}s")
            print("  Consider:")
            print("  - Limiting area size in UI")
            print("  - Adding progress indicators")
            print("  - Using approximation algorithms for large areas")
    
    return results


if __name__ == "__main__":
    results = test_cpp_solver()
    
    # Return exit code based on success
    if results and results[0]['success']:  # At least tiny should work
        sys.exit(0)
    else:
        sys.exit(1)