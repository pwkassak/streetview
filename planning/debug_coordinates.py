#!/usr/bin/env python3
"""
Debug script to check node attributes after graph projection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from map_loader import MapLoader

# Load a small area
loader = MapLoader()
lat, lon = 37.8716, -122.2727
radius = 100  # Small radius for testing

print("Loading graph...")
graph = loader.load_by_point(lat, lon, radius)

# Check first few nodes
print("\nNode attributes after projection:")
for i, (node_id, node_data) in enumerate(graph.nodes(data=True)):
    if i < 3:  # Just check first 3 nodes
        print(f"\nNode {node_id}:")
        for key, value in node_data.items():
            print(f"  {key}: {value}")
    else:
        break

print("\n\nAvailable attributes on all nodes:")
all_keys = set()
for node_id, node_data in graph.nodes(data=True):
    all_keys.update(node_data.keys())
print(sorted(all_keys))