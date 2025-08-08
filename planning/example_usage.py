#!/usr/bin/env python3
"""
Example usage of the StreetView route planning system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from route_planner import RoutePlanner
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


def example_small_area():
    """Example: Plan route for a small area using a point and radius."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Small Area Route Planning")
    print("="*60)
    
    # Initialize planner
    planner = RoutePlanner(network_type='drive')
    
    # Load a small area around a point (e.g., downtown area)
    # Using coordinates for a small area in Berkeley, CA
    lat, lon = 37.8716, -122.2727
    radius = 500  # 500 meters radius
    
    print(f"\nLoading street network around ({lat}, {lon}) with {radius}m radius...")
    planner.load_area_by_point(lat, lon, radius)
    
    # Get area statistics
    stats = planner.get_area_stats()
    print(f"\nArea loaded successfully!")
    print(f"  Nodes: {stats['n_nodes']}")
    print(f"  Edges: {stats['n_edges']}")
    print(f"  Total street length: {stats['total_edge_length']:.0f} meters")
    print(f"  Is Eulerian: {stats['is_eulerian']}")
    
    # Plan the route
    print("\nPlanning optimal route...")
    route = planner.plan_route()
    print(f"Route planned with {len(route)} edges")
    
    # Get route statistics
    route_stats = planner.get_route_stats()
    print(f"\nRoute Statistics:")
    print(f"  Total distance: {route_stats['total_distance']:.0f} meters")
    print(f"  Unique edges covered: {route_stats['unique_edges']}")
    print(f"  Repeated edges: {route_stats['repeated_edges']}")
    print(f"  Coverage: {route_stats['edge_coverage']:.1f}%")
    
    # Export route
    print("\nExporting route to various formats...")
    output_files = planner.export_route(
        output_dir="output/example1",
        formats=['gpx', 'kml', 'geojson', 'html']
    )
    
    print("\nExported files:")
    for fmt, filepath in output_files.items():
        print(f"  {fmt.upper()}: {filepath}")


def example_named_place():
    """Example: Plan route for a named place."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Named Place Route Planning")
    print("="*60)
    
    # Initialize planner
    planner = RoutePlanner(network_type='drive')
    
    # Small neighborhood example
    place_name = "Rockridge, Oakland, California, USA"
    
    print(f"\nProcessing route for: {place_name}")
    print("This may take a moment...")
    
    try:
        # Run full pipeline
        results = planner.full_pipeline(
            place_name=place_name,
            output_dir="output/example2",
            formats=['gpx', 'kml', 'html']
        )
        
        print(f"\n✓ Route planning complete!")
        print(f"  Total distance: {results['route_stats']['total_distance']:.0f} meters")
        print(f"  Files saved to: output/example2/")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Try a smaller area or check your internet connection")


def example_bounding_box():
    """Example: Plan route for a bounding box area."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Bounding Box Route Planning")
    print("="*60)
    
    # Initialize planner
    planner = RoutePlanner(network_type='drive')
    
    # Define a small bounding box (part of Berkeley campus area)
    north = 37.8750
    south = 37.8700
    east = -122.2550
    west = -122.2600
    
    print(f"\nLoading area within bounding box:")
    print(f"  North: {north}, South: {south}")
    print(f"  East: {east}, West: {west}")
    
    planner.load_area_by_bbox(north, south, east, west)
    
    # Get area statistics
    stats = planner.get_area_stats()
    print(f"\nArea loaded: {stats['n_nodes']} nodes, {stats['n_edges']} edges")
    
    # Plan and export route
    planner.plan_route()
    
    output_files = planner.export_route(
        output_dir="output/example3",
        formats=['gpx', 'html']
    )
    
    print(f"\n✓ Route exported to: output/example3/")


def main():
    """Run examples."""
    print("\n" + "="*60)
    print("STREETVIEW ROUTE PLANNING EXAMPLES")
    print("="*60)
    
    # Check if output directory exists, create if not
    os.makedirs("output", exist_ok=True)
    
    # Run examples
    try:
        # Example 1: Small area around a point
        example_small_area()
        
        # Example 2: Named place (uncomment to run)
        # example_named_place()
        
        # Example 3: Bounding box (uncomment to run)
        # example_bounding_box()
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        print("Make sure you have internet connection for downloading OSM data")
    
    print("\n" + "="*60)
    print("Examples complete! Check the output/ directory for results.")
    print("="*60)


if __name__ == "__main__":
    main()