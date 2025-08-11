"""
Module for exporting routes to various formats (GPX, KML, GeoJSON).
"""

import gpxpy
import gpxpy.gpx
import json
import osmnx as ox
import networkx as nx
from typing import List, Tuple, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RouteExporter:
    """Export routes to various formats for navigation and visualization."""
    
    def __init__(self, graph: nx.MultiDiGraph):
        """
        Initialize route exporter.
        
        Args:
            graph: NetworkX graph with geographic data
        """
        self.graph = graph
        
    def export_to_gpx(self, route: List[Tuple[int, int]], 
                      output_file: str,
                      route_name: str = "StreetView Route") -> None:
        """
        Export route to GPX format.
        
        Args:
            route: List of edge tuples (node_from, node_to)
            output_file: Path to output GPX file
            route_name: Name for the route
        """
        logger.info(f"Exporting route to GPX: {output_file}")
        
        # Create GPX object
        gpx = gpxpy.gpx.GPX()
        
        # Create GPX track
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = route_name
        gpx.tracks.append(gpx_track)
        
        # Create GPX segment
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        
        # Add points from route
        added_nodes = set()
        for u, v in route:
            # Add starting node
            if u not in added_nodes:
                node_data = self.graph.nodes[u]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
                    added_nodes.add(u)
            
            # Add ending node
            if v not in added_nodes:
                node_data = self.graph.nodes[v]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
                    added_nodes.add(v)
            
            # Add intermediate points along edge if available
            if self.graph.has_edge(u, v):
                edge_data = self.graph[u][v][0]  # Get first edge if multiple
                if 'geometry' in edge_data:
                    # Extract intermediate points from geometry
                    try:
                        coords = list(edge_data['geometry'].coords)
                        for lon, lat in coords[1:-1]:  # Skip first and last (already added)
                            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
                    except:
                        pass
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(gpx.to_xml())
        
        logger.info(f"GPX file saved with {len(gpx_segment.points)} points")
    
    def export_to_kml(self, route: List[Tuple[int, int]], 
                      output_file: str,
                      route_name: str = "StreetView Route") -> None:
        """
        Export route to KML format.
        
        Args:
            route: List of edge tuples (node_from, node_to)
            output_file: Path to output KML file
            route_name: Name for the route
        """
        logger.info(f"Exporting route to KML: {output_file}")
        
        kml_template = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <description>Route generated for street coverage</description>
    <Style id="route">
      <LineStyle>
        <color>ff0000ff</color>
        <width>4</width>
      </LineStyle>
    </Style>
    <Placemark>
      <name>{name}</name>
      <styleUrl>#route</styleUrl>
      <LineString>
        <coordinates>
{coordinates}
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""
        
        # Build coordinate string
        coords = []
        added_nodes = set()
        
        for u, v in route:
            # Add starting node
            if u not in added_nodes:
                node_data = self.graph.nodes[u]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    coords.append(f"          {lon},{lat},0")
                    added_nodes.add(u)
            
            # Add ending node
            if v not in added_nodes:
                node_data = self.graph.nodes[v]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    coords.append(f"          {lon},{lat},0")
                    added_nodes.add(v)
        
        # Write KML file
        kml_content = kml_template.format(
            name=route_name,
            coordinates="\n".join(coords)
        )
        
        with open(output_file, 'w') as f:
            f.write(kml_content)
        
        logger.info(f"KML file saved with {len(coords)} points")
    
    def export_to_geojson(self, route: List[Tuple[int, int]], 
                          output_file: str,
                          route_name: str = "StreetView Route",
                          include_segments: bool = False) -> None:
        """
        Export route to GeoJSON format with street geometry.
        
        Args:
            route: List of edge tuples (node_from, node_to)
            output_file: Path to output GeoJSON file
            route_name: Name for the route
            include_segments: If True, export as separate segments with traversal metadata
        """
        logger.info(f"Exporting route to GeoJSON: {output_file}")
        
        # Check if graph is projected and create transformer if needed
        crs = self.graph.graph.get('crs', 'EPSG:4326')
        transformer = None
        if crs != 'EPSG:4326' and crs != 'epsg:4326':
            from pyproj import Transformer
            transformer = Transformer.from_crs(crs, 'EPSG:4326', always_xy=True)
            logger.info(f"Graph is projected ({crs}), will transform coordinates to lat/lon")
        
        # Track edge traversals for segment analysis
        edge_traversals = {}  # (u, v) -> [traversal_indices]
        segments = []  # List of segments with metadata
        
        # Build coordinate list using street geometry
        coordinates = []
        last_node = None
        
        for idx, (u, v) in enumerate(route):
            # Track traversals
            edge_key = (min(u, v), max(u, v))  # Normalize edge direction
            if edge_key not in edge_traversals:
                edge_traversals[edge_key] = []
            edge_traversals[edge_key].append(idx)
            traversal_count = len(edge_traversals[edge_key])
            
            # Store segment coordinates
            segment_coords = []
            # Try to get edge geometry for actual street path
            if self.graph.has_edge(u, v):
                edge_data = self.graph[u][v]
                # Handle multi-edge case
                if isinstance(edge_data, dict) and 'geometry' in edge_data:
                    geometry = edge_data['geometry']
                else:
                    # Try to find an edge with geometry
                    geometry = None
                    for key in edge_data:
                        if 'geometry' in edge_data[key]:
                            geometry = edge_data[key]['geometry']
                            break
                
                # If we have geometry, use it
                if geometry:
                    try:
                        # Get coordinates from the geometry
                        edge_coords = list(geometry.coords)
                        
                        # Transform coordinates if graph is projected
                        if transformer:
                            transformed_coords = []
                            for x, y in edge_coords:
                                lon, lat = transformer.transform(x, y)
                                transformed_coords.append((lon, lat))
                            edge_coords = transformed_coords
                        
                        # Skip first point if it's the same as last point (avoid duplicates)
                        if coordinates and len(edge_coords) > 0:
                            last_point = coordinates[-1]
                            first_point = [edge_coords[0][0], edge_coords[0][1]]
                            if abs(last_point[0] - first_point[0]) < 0.000001 and abs(last_point[1] - first_point[1]) < 0.000001:
                                edge_coords = edge_coords[1:]
                        
                        # Add all points from the geometry
                        for lon, lat in edge_coords:
                            coord = [lon, lat]
                            coordinates.append(coord)
                            segment_coords.append(coord)
                        
                        # Add segment metadata if requested
                        if include_segments and segment_coords:
                            segment_data = {
                                'index': idx,
                                'from_node': u,
                                'to_node': v,
                                'traversal_number': traversal_count,
                                'edge_key': f"{edge_key[0]}_{edge_key[1]}",
                                'coordinates': segment_coords[:]
                            }
                            # Get street name if available
                            if isinstance(edge_data, dict):
                                segment_data['street_name'] = edge_data.get('name', '')
                            else:
                                for key in edge_data:
                                    if 'name' in edge_data[key]:
                                        segment_data['street_name'] = edge_data[key]['name']
                                        break
                            segments.append(segment_data)
                        continue
                    except Exception as e:
                        logger.debug(f"Could not extract geometry for edge {u}->{v}: {e}")
            
            # Fallback: use node coordinates if no geometry available
            if last_node != u:
                node_data = self.graph.nodes[u]
                if transformer:
                    # Graph is projected, use x/y and transform
                    x = node_data.get('x')
                    y = node_data.get('y')
                    if x is not None and y is not None:
                        lon, lat = transformer.transform(x, y)
                        coord = [lon, lat]
                        coordinates.append(coord)
                        segment_coords.append(coord)
                else:
                    # Graph is not projected, use lat/lon directly
                    lat = node_data.get('lat', node_data.get('y'))
                    lon = node_data.get('lon', node_data.get('x'))
                    if lat and lon:
                        coord = [lon, lat]
                        coordinates.append(coord)
                        segment_coords.append(coord)
            
            node_data = self.graph.nodes[v]
            if transformer:
                # Graph is projected, use x/y and transform
                x = node_data.get('x')
                y = node_data.get('y')
                if x is not None and y is not None:
                    lon, lat = transformer.transform(x, y)
                    coord = [lon, lat]
                    coordinates.append(coord)
                    segment_coords.append(coord)
            else:
                # Graph is not projected, use lat/lon directly
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    coord = [lon, lat]
                    coordinates.append(coord)
                    segment_coords.append(coord)
            
            # Add segment for fallback case
            if include_segments and segment_coords:
                segments.append({
                    'index': idx,
                    'from_node': u,
                    'to_node': v,
                    'traversal_number': traversal_count,
                    'edge_key': f"{edge_key[0]}_{edge_key[1]}",
                    'coordinates': segment_coords[:],
                    'street_name': ''
                })
            
            last_node = v
        
        # Create GeoJSON structure
        if include_segments:
            # Export as separate segments
            features = []
            for segment in segments:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "segment_index": segment['index'],
                        "from_node": segment['from_node'],
                        "to_node": segment['to_node'],
                        "traversal_number": segment['traversal_number'],
                        "edge_key": segment['edge_key'],
                        "street_name": segment.get('street_name', '')
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": segment['coordinates']
                    }
                })
            
            geojson = {
                "type": "FeatureCollection",
                "properties": {
                    "name": route_name,
                    "timestamp": datetime.now().isoformat(),
                    "total_segments": len(segments),
                    "total_edges": len(route),
                    "unique_edges": len(edge_traversals),
                    "max_traversals": max(len(traversals) for traversals in edge_traversals.values()) if edge_traversals else 0
                },
                "features": features
            }
        else:
            # Export as single line (existing behavior)
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "name": route_name,
                            "timestamp": datetime.now().isoformat(),
                            "total_points": len(coordinates),
                            "total_edges": len(route)
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coordinates
                        }
                    }
                ]
            }
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        logger.info(f"GeoJSON file saved with {len(coordinates)} points")
    
    def export_to_csv(self, route: List[Tuple[int, int]], 
                      output_file: str) -> None:
        """
        Export route to CSV format with waypoints.
        
        Args:
            route: List of edge tuples (node_from, node_to)
            output_file: Path to output CSV file
        """
        logger.info(f"Exporting route to CSV: {output_file}")
        
        import csv
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['waypoint_id', 'latitude', 'longitude', 'from_node', 'to_node']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            waypoint_id = 0
            for u, v in route:
                # Write from node
                node_data = self.graph.nodes[u]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                
                if lat and lon:
                    writer.writerow({
                        'waypoint_id': waypoint_id,
                        'latitude': lat,
                        'longitude': lon,
                        'from_node': u,
                        'to_node': v
                    })
                    waypoint_id += 1
        
        logger.info(f"CSV file saved with {waypoint_id} waypoints")
    
    def visualize_route_folium(self, route: List[Tuple[int, int]], 
                               output_file: str = "route_map.html") -> None:
        """
        Create an interactive Folium map of the route.
        
        Args:
            route: List of edge tuples (node_from, node_to)
            output_file: Path to output HTML file
        """
        import folium
        
        logger.info(f"Creating interactive map: {output_file}")
        
        # Get coordinates for centering map
        first_node = route[0][0]
        node_data = self.graph.nodes[first_node]
        center_lat = node_data.get('lat', node_data.get('y'))
        center_lon = node_data.get('lon', node_data.get('x'))
        
        # Create folium map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
        
        # Add route as polyline
        route_coords = []
        for u, v in route:
            for node in [u, v]:
                node_data = self.graph.nodes[node]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    route_coords.append([lat, lon])
        
        # Add the route
        folium.PolyLine(
            route_coords,
            color='blue',
            weight=3,
            opacity=0.8,
            popup='StreetView Route'
        ).add_to(m)
        
        # Add start and end markers
        if route_coords:
            folium.Marker(
                route_coords[0],
                popup='Start',
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)
            
            folium.Marker(
                route_coords[-1],
                popup='End',
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)
        
        # Save map
        m.save(output_file)
        logger.info(f"Interactive map saved to {output_file}")