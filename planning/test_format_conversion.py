#!/usr/bin/env python3
"""
Test the data format conversion pipeline.
Verifies NetworkX → CSV → postman_problems flow works correctly.
"""

import networkx as nx
import pandas as pd
import tempfile
import os
import sys
from postman_problems.solver import cpp

def test_simple_graph():
    """Test with a simple, known graph."""
    print("="*60)
    print("SIMPLE GRAPH TEST")
    print("="*60)
    
    # Create a simple triangle graph (Eulerian)
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, length=100, name="Edge_1_2")
    G.add_edge(2, 3, length=150, name="Edge_2_3")
    G.add_edge(3, 1, length=200, name="Edge_3_1")
    
    print("Created simple triangle graph:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    
    # Test conversion to DataFrame
    print("\n1. Testing NetworkX → DataFrame conversion...")
    try:
        edges = []
        for u, v, key, data in G.edges(keys=True, data=True):
            edges.append({
                'node_from': u,
                'node_to': v,
                'distance': data.get('length', 1.0),
                'name': data.get('name', '')
            })
        df = pd.DataFrame(edges)
        print(f"  ✓ Converted to DataFrame with {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        print("\nDataFrame content:")
        print(df)
    except Exception as e:
        print(f"  ✗ Conversion failed: {e}")
        return False
    
    # Test CSV write/read
    print("\n2. Testing DataFrame → CSV → postman_problems...")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            df.to_csv(f, index=False)
        
        print(f"  CSV written to: {temp_path}")
        
        # Test solving with postman_problems
        circuit, graph = cpp(temp_path, edge_weight='distance')
        
        print(f"  ✓ CPP solved successfully")
        print(f"  Circuit length: {len(circuit)} edges")
        print(f"  Circuit: {[f'{e[0]}→{e[1]}' for e in circuit]}")
        
        # Clean up
        os.remove(temp_path)
        
    except Exception as e:
        print(f"  ✗ CSV/CPP failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
    
    return True


def test_non_eulerian_graph():
    """Test with a non-Eulerian graph that needs augmentation."""
    print("\n" + "="*60)
    print("NON-EULERIAN GRAPH TEST")
    print("="*60)
    
    # Create a star graph (all nodes except center have odd degree)
    G = nx.MultiDiGraph()
    # Center node is 0, connected to 1,2,3,4
    for i in range(1, 5):
        G.add_edge(0, i, length=100*i)
        G.add_edge(i, 0, length=100*i)  # Make bidirectional
    
    print("Created star graph (non-Eulerian):")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    
    # Check degrees
    degrees = dict(G.degree())
    odd_nodes = [n for n, d in degrees.items() if d % 2 == 1]
    print(f"  Odd-degree nodes: {odd_nodes}")
    
    # Convert and solve
    print("\nTesting CPP on non-Eulerian graph...")
    try:
        edges = []
        for u, v, key, data in G.edges(keys=True, data=True):
            edges.append({
                'node_from': u,
                'node_to': v,
                'distance': data.get('length', 1.0)
            })
        df = pd.DataFrame(edges)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            df.to_csv(f, index=False)
        
        circuit, graph = cpp(temp_path, edge_weight='distance')
        
        print(f"  ✓ CPP solved non-Eulerian graph")
        print(f"  Original edges: {G.number_of_edges()}")
        print(f"  Circuit length: {len(circuit)} edges")
        print(f"  Extra edges added: {len(circuit) - G.number_of_edges()}")
        
        os.remove(temp_path)
        return True
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def test_real_osm_graph():
    """Test with a real graph from OSM."""
    print("\n" + "="*60)
    print("REAL OSM GRAPH TEST")
    print("="*60)
    
    from map_loader import MapLoader
    
    # Load a tiny area
    print("Loading small Berkeley area...")
    loader = MapLoader('drive')
    
    try:
        # Small area - Downtown Berkeley (known to have streets)
        graph = loader.load_by_bbox(37.8716, 37.8696, -122.2676, -122.2696)
        print(f"  Loaded graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        
    except Exception as e:
        print(f"  ✗ Failed to load OSM data: {e}")
        return False
    
    # Test conversion
    print("\nConverting OSM graph for postman_problems...")
    try:
        edges = []
        for u, v, key, data in graph.edges(keys=True, data=True):
            edges.append({
                'node_from': str(u),  # Convert to string as postman_problems expects
                'node_to': str(v),
                'distance': data.get('length', 1.0)
            })
        
        df = pd.DataFrame(edges)
        print(f"  Created DataFrame with {len(df)} edges")
        
        # Check for any issues
        if df['distance'].isna().any():
            print("  ⚠️ Warning: Some edges have no distance")
        if df['distance'].min() <= 0:
            print("  ⚠️ Warning: Some edges have zero or negative distance")
        
        print(f"  Distance range: {df['distance'].min():.1f} - {df['distance'].max():.1f} meters")
        
        # Test with postman_problems
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            df.to_csv(f, index=False)
        
        print("\nSolving with postman_problems...")
        circuit, augmented = cpp(temp_path, edge_weight='distance')
        
        print(f"  ✓ Successfully solved OSM graph")
        print(f"  Circuit: {len(circuit)} edges")
        
        os.remove(temp_path)
        return True
        
    except Exception as e:
        print(f"  ✗ Conversion/solving failed: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def main():
    """Run all format conversion tests."""
    print("FORMAT CONVERSION PIPELINE TEST")
    print("Testing NetworkX → CSV → postman_problems flow")
    print("")
    
    results = []
    
    # Test 1: Simple graph
    results.append(("Simple Eulerian Graph", test_simple_graph()))
    
    # Test 2: Non-Eulerian graph
    results.append(("Non-Eulerian Graph", test_non_eulerian_graph()))
    
    # Test 3: Real OSM graph
    results.append(("Real OSM Graph", test_real_osm_graph()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{name:30} {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n✓ All format conversion tests passed!")
        print("The data pipeline is working correctly.")
    else:
        print("\n✗ Some tests failed!")
        print("Check the conversion pipeline for issues.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())