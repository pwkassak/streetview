#!/usr/bin/env python3
"""
Debug script to test graph projection and coordinate preservation.
"""

import osmnx as ox

# Load a small area
lat, lon = 37.8716, -122.2727
radius = 100

print("Loading unprojected graph...")
graph = ox.graph_from_point((lat, lon), dist=radius, network_type='drive')

# Check node before projection
first_node = list(graph.nodes())[0]
print(f"\nBefore projection - Node {first_node}:")
print(f"  x: {graph.nodes[first_node].get('x')}")
print(f"  y: {graph.nodes[first_node].get('y')}")
print(f"  lon: {graph.nodes[first_node].get('lon')}")
print(f"  lat: {graph.nodes[first_node].get('lat')}")

# Project graph
print("\nProjecting graph to UTM...")
graph_proj = ox.project_graph(graph)

# Check same node after projection
print(f"\nAfter projection - Node {first_node}:")
print(f"  x: {graph_proj.nodes[first_node].get('x')}")
print(f"  y: {graph_proj.nodes[first_node].get('y')}")
print(f"  lon: {graph_proj.nodes[first_node].get('lon')}")
print(f"  lat: {graph_proj.nodes[first_node].get('lat')}")

# Check if there's a way to get back to lat/lon
print("\nGraph CRS info:")
print(f"  CRS: {graph_proj.graph.get('crs')}")

# Try to unproject back
print("\nTrying to unproject back to lat/lon...")
graph_unproj = ox.project_graph(graph_proj, to_latlong=True)
print(f"\nAfter unprojection - Node {first_node}:")
print(f"  x: {graph_unproj.nodes[first_node].get('x')}")
print(f"  y: {graph_unproj.nodes[first_node].get('y')}")
print(f"  lon: {graph_unproj.nodes[first_node].get('lon')}")
print(f"  lat: {graph_unproj.nodes[first_node].get('lat')}")