"""
Main route planning module that integrates map loading, CPP solving, and route export.
"""

import os
from typing import Optional, Union, Tuple, List
import logging
from map_loader import MapLoader
from cpp_solver import CPPSolver
from route_exporter import RouteExporter
import networkx as nx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoutePlanner:
    """Main class for planning routes that cover all streets in an area."""
    
    def __init__(self, network_type: str = 'drive'):
        """
        Initialize route planner.
        
        Args:
            network_type: Type of network ('drive', 'walk', 'bike', etc.)
        """
        self.network_type = network_type
        self.map_loader = MapLoader(network_type)
        self.graph = None
        self.solver = None
        self.route = None
        self.exporter = None
        
    def load_area_by_place(self, place_name: str) -> nx.MultiDiGraph:
        """
        Load street network for a named place.
        
        Args:
            place_name: Name of place (e.g., "Piedmont, California, USA")
            
        Returns:
            Loaded graph
        """
        logger.info(f"Loading area: {place_name}")
        self.graph = self.map_loader.load_by_place(place_name)
        self._setup_solver_and_exporter()
        return self.graph
    
    def load_area_by_bbox(self, north: float, south: float, 
                         east: float, west: float) -> nx.MultiDiGraph:
        """
        Load street network within a bounding box.
        
        Args:
            north: Northern latitude
            south: Southern latitude
            east: Eastern longitude
            west: Western longitude
            
        Returns:
            Loaded graph
        """
        logger.info(f"Loading area by bounding box")
        self.graph = self.map_loader.load_by_bbox(north, south, east, west)
        self._setup_solver_and_exporter()
        return self.graph
    
    def load_area_by_point(self, lat: float, lon: float, 
                          radius_m: float = 1000) -> nx.MultiDiGraph:
        """
        Load street network around a point.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_m: Radius in meters
            
        Returns:
            Loaded graph
        """
        logger.info(f"Loading area around point ({lat}, {lon})")
        self.graph = self.map_loader.load_by_point(lat, lon, radius_m)
        self._setup_solver_and_exporter()
        return self.graph
    
    def _setup_solver_and_exporter(self):
        """Setup solver and exporter after graph is loaded."""
        if self.graph:
            self.solver = CPPSolver(self.graph)
            self.exporter = RouteExporter(self.graph)
    
    def plan_route(self) -> List[Tuple[int, int]]:
        """
        Plan optimal route covering all streets.
        
        Returns:
            List of edges representing the route
        """
        if not self.graph:
            raise ValueError("No area loaded. Load an area first.")
        
        logger.info("Planning route...")
        self.route = self.solver.solve()
        
        # Get and display statistics
        stats = self.solver.get_route_stats()
        logger.info(f"Route statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        return self.route
    
    def export_route(self, output_dir: str = "output", 
                    formats: List[str] = None,
                    base_name: str = "route") -> dict:
        """
        Export route to various formats.
        
        Args:
            output_dir: Directory for output files
            formats: List of formats to export ('gpx', 'kml', 'geojson', 'csv', 'html')
            base_name: Base name for output files
            
        Returns:
            Dictionary mapping format to file path
        """
        if not self.route:
            raise ValueError("No route planned. Plan a route first.")
        
        if formats is None:
            formats = ['gpx', 'kml', 'geojson', 'html']
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = {}
        
        for fmt in formats:
            if fmt == 'gpx':
                output_file = os.path.join(output_dir, f"{base_name}.gpx")
                self.exporter.export_to_gpx(self.route, output_file)
                output_files['gpx'] = output_file
                
            elif fmt == 'kml':
                output_file = os.path.join(output_dir, f"{base_name}.kml")
                self.exporter.export_to_kml(self.route, output_file)
                output_files['kml'] = output_file
                
            elif fmt == 'geojson':
                output_file = os.path.join(output_dir, f"{base_name}.geojson")
                self.exporter.export_to_geojson(self.route, output_file)
                output_files['geojson'] = output_file
                
            elif fmt == 'csv':
                output_file = os.path.join(output_dir, f"{base_name}.csv")
                self.exporter.export_to_csv(self.route, output_file)
                output_files['csv'] = output_file
                
            elif fmt == 'html':
                output_file = os.path.join(output_dir, f"{base_name}_map.html")
                self.exporter.visualize_route_folium(self.route, output_file)
                output_files['html'] = output_file
        
        logger.info(f"Routes exported to {output_dir}")
        return output_files
    
    def get_area_stats(self) -> dict:
        """
        Get statistics about the loaded area.
        
        Returns:
            Dictionary with area statistics
        """
        if not self.graph:
            raise ValueError("No area loaded. Load an area first.")
        
        return self.map_loader.get_graph_stats(self.graph)
    
    def get_route_stats(self) -> dict:
        """
        Get statistics about the planned route.
        
        Returns:
            Dictionary with route statistics
        """
        if not self.solver or not self.route:
            raise ValueError("No route planned. Plan a route first.")
        
        return self.solver.get_route_stats()
    
    def full_pipeline(self, place_name: str, 
                     output_dir: str = "output",
                     formats: List[str] = None) -> dict:
        """
        Run full pipeline: load area, plan route, export.
        
        Args:
            place_name: Name of place to plan route for
            output_dir: Directory for outputs
            formats: Export formats
            
        Returns:
            Dictionary with results
        """
        # Load area
        self.load_area_by_place(place_name)
        
        # Get area stats
        area_stats = self.get_area_stats()
        logger.info(f"\nArea statistics for {place_name}:")
        for key, value in area_stats.items():
            if key != 'odd_degree_nodes':  # Skip the node list for cleaner output
                logger.info(f"  {key}: {value}")
        
        # Plan route
        self.plan_route()
        
        # Export route
        output_files = self.export_route(output_dir, formats, 
                                        base_name=place_name.replace(", ", "_").replace(" ", "_"))
        
        # Return results
        return {
            'place': place_name,
            'area_stats': area_stats,
            'route_stats': self.get_route_stats(),
            'output_files': output_files
        }