"""
Module for loading street network data from OpenStreetMap.
"""

import osmnx as ox
import networkx as nx
from typing import Union, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapLoader:
    """Handles loading and preprocessing of street network data from OSM."""
    
    def __init__(self, network_type: str = 'drive'):
        """
        Initialize MapLoader.
        
        Args:
            network_type: Type of street network to load.
                Options: 'drive', 'drive_service', 'walk', 'bike', 'all'
        """
        self.network_type = network_type
        ox.settings.use_cache = True
        ox.settings.log_console = False
        
    def load_by_place(self, place_name: str) -> nx.MultiDiGraph:
        """
        Load street network for a named place.
        
        Args:
            place_name: Name of place (e.g., "Piedmont, California, USA")
            
        Returns:
            NetworkX MultiDiGraph representing the street network
        """
        logger.info(f"Loading street network for {place_name}")
        graph = ox.graph_from_place(place_name, network_type=self.network_type)
        return self._preprocess_graph(graph)
    
    def load_by_bbox(self, north: float, south: float, 
                     east: float, west: float) -> nx.MultiDiGraph:
        """
        Load street network within a bounding box.
        
        Args:
            north: Northern latitude boundary
            south: Southern latitude boundary
            east: Eastern longitude boundary
            west: Western longitude boundary
            
        Returns:
            NetworkX MultiDiGraph representing the street network
        """
        logger.info(f"Loading street network for bbox: N={north}, S={south}, E={east}, W={west}")
        # OSMnx expects bbox as (west, south, east, north) - i.e., (left, bottom, right, top)
        graph = ox.graph_from_bbox(bbox=(west, south, east, north), 
                                   network_type=self.network_type)
        return self._preprocess_graph(graph)
    
    def load_by_polygon(self, polygon) -> nx.MultiDiGraph:
        """
        Load street network within a polygon.
        
        Args:
            polygon: Shapely Polygon object defining the area
            
        Returns:
            NetworkX MultiDiGraph representing the street network
        """
        logger.info("Loading street network for polygon area")
        graph = ox.graph_from_polygon(polygon, network_type=self.network_type)
        return self._preprocess_graph(graph)
    
    def load_by_point(self, lat: float, lon: float, 
                      dist: float = 1000) -> nx.MultiDiGraph:
        """
        Load street network within a distance from a point.
        
        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            dist: Distance in meters from the point
            
        Returns:
            NetworkX MultiDiGraph representing the street network
        """
        logger.info(f"Loading street network around point ({lat}, {lon}) with {dist}m radius")
        graph = ox.graph_from_point((lat, lon), dist=dist, 
                                    network_type=self.network_type)
        return self._preprocess_graph(graph)
    
    def _preprocess_graph(self, graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """
        Preprocess the graph for routing.
        
        Args:
            graph: Raw graph from OSM
            
        Returns:
            Preprocessed graph
        """
        # Store original lat/lon before projection
        for node_id, node_data in graph.nodes(data=True):
            node_data['lat'] = node_data.get('y')
            node_data['lon'] = node_data.get('x')
        
        # Project to UTM for accurate distance calculations
        graph = ox.project_graph(graph)
        
        # Add edge lengths if not present
        if 'length' not in next(iter(graph.edges(data=True)))[2]:
            graph = ox.distance.add_edge_lengths(graph)
        
        # Simplify graph topology if not already simplified
        try:
            graph = ox.simplify_graph(graph)
        except:
            # Graph is already simplified, skip
            pass
        
        logger.info(f"Graph loaded: {graph.number_of_nodes()} nodes, "
                   f"{graph.number_of_edges()} edges")
        
        return graph
    
    def get_graph_stats(self, graph: nx.MultiDiGraph) -> dict:
        """
        Get basic statistics about the graph.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            Dictionary with graph statistics
        """
        stats = {
            'n_nodes': graph.number_of_nodes(),
            'n_edges': graph.number_of_edges(),
            'total_edge_length': sum(data['length'] for _, _, data in graph.edges(data=True)),
            'is_strongly_connected': nx.is_strongly_connected(graph),
            'is_eulerian': nx.is_eulerian(graph)
        }
        
        # Count odd-degree nodes (important for Chinese Postman Problem)
        in_degrees = dict(graph.in_degree())
        out_degrees = dict(graph.out_degree())
        odd_nodes = []
        for node in graph.nodes():
            total_degree = in_degrees[node] + out_degrees[node]
            if total_degree % 2 == 1:
                odd_nodes.append(node)
        
        stats['n_odd_degree_nodes'] = len(odd_nodes)
        stats['odd_degree_nodes'] = odd_nodes[:10]  # Show first 10 for brevity
        
        return stats