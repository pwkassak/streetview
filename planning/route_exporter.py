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
                          route_name: str = "StreetView Route") -> None:
        """
        Export route to GeoJSON format.
        
        Args:
            route: List of edge tuples (node_from, node_to)
            output_file: Path to output GeoJSON file
            route_name: Name for the route
        """
        logger.info(f"Exporting route to GeoJSON: {output_file}")
        
        # Build coordinate list
        coordinates = []
        added_nodes = set()
        
        for u, v in route:
            # Add starting node
            if u not in added_nodes:
                node_data = self.graph.nodes[u]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    coordinates.append([lon, lat])
                    added_nodes.add(u)
            
            # Add ending node
            if v not in added_nodes:
                node_data = self.graph.nodes[v]
                lat = node_data.get('lat', node_data.get('y'))
                lon = node_data.get('lon', node_data.get('x'))
                if lat and lon:
                    coordinates.append([lon, lat])
                    added_nodes.add(v)
        
        # Create GeoJSON structure
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