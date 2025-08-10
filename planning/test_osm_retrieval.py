#!/usr/bin/env python3
"""
Test OSM data retrieval in isolation.
Tests progressively larger areas in Berkeley to understand performance.
"""

import time
import sys
from map_loader import MapLoader

def test_osm_retrieval():
    """Test loading street data from OSM for known Berkeley areas."""
    
    print("="*60)
    print("OSM DATA RETRIEVAL TEST")
    print("="*60)
    
    # Test areas in Berkeley (progressively larger)
    # Using known good coordinates centered on major streets
    test_areas = [
        {
            "name": "Small (2-3 blocks)",
            "north": 37.8716,
            "south": 37.8696,
            "east": -122.2676,
            "west": -122.2696,
            "description": "Downtown Berkeley - Shattuck & Center St"
        },
        {
            "name": "Medium (10-15 blocks)",
            "north": 37.8687,
            "south": 37.8637,
            "east": -122.2573,
            "west": -122.2623,
            "description": "Telegraph Avenue commercial district"
        },
        {
            "name": "Large (50+ blocks)",
            "north": 37.8749,
            "south": 37.8669,
            "east": -122.2547,
            "west": -122.2627,
            "description": "UC Berkeley campus and surroundings"
        },
        {
            "name": "Extra Large (200+ blocks)",
            "north": 37.8800,
            "south": 37.8600,
            "east": -122.2500,
            "west": -122.2700,
            "description": "Greater Berkeley area"
        }
    ]
    
    loader = MapLoader('drive')
    results = []
    
    for area in test_areas:
        print(f"\n--- Testing {area['name']} ---")
        print(f"Description: {area['description']}")
        print(f"Bounds: N={area['north']}, S={area['south']}, E={area['east']}, W={area['west']}")
        
        # Estimate area size
        km_n_s = abs(area['north'] - area['south']) * 111
        km_e_w = abs(area['east'] - area['west']) * 111 * 0.7  # Rough longitude adjustment
        area_km2 = km_n_s * km_e_w
        print(f"Approximate area: {area_km2:.2f} km²")
        
        try:
            start_time = time.time()
            graph = loader.load_by_bbox(
                area['north'], 
                area['south'], 
                area['east'], 
                area['west']
            )
            load_time = time.time() - start_time
            
            # Get statistics
            n_nodes = graph.number_of_nodes()
            n_edges = graph.number_of_edges()
            
            # Check if graph has data
            if n_edges == 0:
                print(f"⚠️ Warning: Graph loaded but contains no edges")
                print(f"  This area may not contain any streets")
                results.append({
                    'name': area['name'],
                    'area_km2': area_km2,
                    'load_time': load_time,
                    'nodes': n_nodes,
                    'edges': n_edges,
                    'length_km': 0,
                    'success': False,
                    'error': 'No edges in graph'
                })
                continue
            
            # Calculate total street length
            total_length = sum(data.get('length', 0) 
                             for u, v, data in graph.edges(data=True))
            
            print(f"✓ Success!")
            print(f"  Loading time: {load_time:.2f} seconds")
            print(f"  Nodes: {n_nodes}")
            print(f"  Edges: {n_edges}")
            print(f"  Total street length: {total_length:.0f} meters ({total_length/1000:.1f} km)")
            print(f"  Avg edge length: {total_length/n_edges if n_edges > 0 else 0:.0f} meters")
            
            results.append({
                'name': area['name'],
                'area_km2': area_km2,
                'load_time': load_time,
                'nodes': n_nodes,
                'edges': n_edges,
                'length_km': total_length/1000,
                'success': True
            })
            
        except Exception as e:
            print(f"✗ Failed: {e}")
            results.append({
                'name': area['name'],
                'area_km2': area_km2,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for result in results:
        if result['success']:
            print(f"{result['name']:20} - {result['load_time']:6.2f}s - "
                  f"{result['nodes']:4} nodes - {result['edges']:4} edges - "
                  f"{result['length_km']:.1f} km streets")
        else:
            print(f"{result['name']:20} - FAILED: {result['error']}")
    
    # Check for performance issues
    print("\n" + "="*60)
    print("PERFORMANCE ANALYSIS")
    print("="*60)
    
    successful_results = [r for r in results if r['success']]
    if successful_results:
        # Check if load time scales reasonably
        if len(successful_results) > 1:
            for i in range(1, len(successful_results)):
                prev = successful_results[i-1]
                curr = successful_results[i]
                time_ratio = curr['load_time'] / prev['load_time'] if prev['load_time'] > 0 else float('inf')
                edge_ratio = curr['edges'] / prev['edges'] if prev['edges'] > 0 else float('inf')
                
                print(f"{prev['name']} → {curr['name']}:")
                print(f"  Time increased {time_ratio:.1f}x")
                print(f"  Edges increased {edge_ratio:.1f}x")
                
                if time_ratio > edge_ratio * 2:
                    print(f"  ⚠️ Performance degradation detected!")
    
    return results


if __name__ == "__main__":
    results = test_osm_retrieval()
    
    # Return exit code based on success
    if all(r['success'] for r in results[:2]):  # At least tiny and small should work
        print("\n✓ Basic OSM retrieval working correctly")
        sys.exit(0)
    else:
        print("\n✗ OSM retrieval has issues")
        sys.exit(1)