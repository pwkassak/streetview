"""
Chinese Postman Problem solver for finding optimal routes that cover all streets.
"""

import networkx as nx
from itertools import combinations
import logging
from typing import List, Tuple, Set, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CPPSolver:
    """Solves the Chinese Postman Problem for street coverage."""
    
    def __init__(self, graph: nx.MultiDiGraph):
        """
        Initialize CPP solver with a street network graph.
        
        Args:
            graph: NetworkX MultiDiGraph representing the street network
        """
        self.graph = graph.copy()
        self.augmented_graph = None
        self.euler_circuit = None
        
    def solve(self) -> List[Tuple[int, int]]:
        """
        Solve the Chinese Postman Problem.
        
        Returns:
            List of edges representing the optimal tour
        """
        logger.info("Starting Chinese Postman Problem solution")
        
        # Check if graph is already Eulerian
        if self._is_eulerian():
            logger.info("Graph is already Eulerian")
            self.augmented_graph = self.graph.copy()
        else:
            logger.info("Graph is not Eulerian, augmenting...")
            self._augment_graph()
        
        # Find Euler circuit
        self.euler_circuit = self._find_euler_circuit()
        logger.info(f"Found Euler circuit with {len(self.euler_circuit)} edges")
        
        return self.euler_circuit
    
    def _is_eulerian(self) -> bool:
        """
        Check if the graph is Eulerian (all vertices have even degree).
        
        Returns:
            True if graph is Eulerian, False otherwise
        """
        # For directed graphs, check if in-degree equals out-degree for all nodes
        for node in self.graph.nodes():
            if self.graph.in_degree(node) != self.graph.out_degree(node):
                return False
        
        # Also check if graph is strongly connected
        return nx.is_strongly_connected(self.graph)
    
    def _get_odd_degree_nodes(self) -> Set[int]:
        """
        Find all nodes with odd total degree.
        
        Returns:
            Set of node IDs with odd degree
        """
        odd_nodes = set()
        for node in self.graph.nodes():
            total_degree = self.graph.in_degree(node) + self.graph.out_degree(node)
            if total_degree % 2 == 1:
                odd_nodes.add(node)
        return odd_nodes
    
    def _augment_graph(self):
        """
        Augment the graph to make it Eulerian by adding minimum weight edges.
        """
        # For simplicity, convert to undirected for finding odd nodes
        undirected = self.graph.to_undirected()
        
        # Find odd degree nodes
        odd_nodes = []
        for node in undirected.nodes():
            if undirected.degree(node) % 2 == 1:
                odd_nodes.append(node)
        
        logger.info(f"Found {len(odd_nodes)} odd-degree nodes")
        
        if not odd_nodes:
            self.augmented_graph = self.graph.copy()
            return
        
        # Find minimum weight matching of odd nodes
        min_weight_pairs = self._find_min_weight_matching(odd_nodes)
        
        # Add duplicate edges to make graph Eulerian
        self.augmented_graph = self.graph.copy()
        for node1, node2, path in min_weight_pairs:
            # Add edges along the shortest path
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                # Find the edge data from original graph
                if self.graph.has_edge(u, v):
                    edge_data = self.graph[u][v][0]  # Get first edge if multiple
                    self.augmented_graph.add_edge(u, v, **edge_data)
                elif self.graph.has_edge(v, u):
                    edge_data = self.graph[v][u][0]
                    self.augmented_graph.add_edge(v, u, **edge_data)
        
        logger.info(f"Added {len(min_weight_pairs)} edge pairs to augment graph")
    
    def _find_min_weight_matching(self, odd_nodes: List[int]) -> List[Tuple]:
        """
        Find minimum weight perfect matching of odd degree nodes.
        
        Args:
            odd_nodes: List of nodes with odd degree
            
        Returns:
            List of (node1, node2, path) tuples for minimum weight matching
        """
        # Compute shortest paths between all pairs of odd nodes
        odd_node_pairs = list(combinations(odd_nodes, 2))
        
        # Create complete graph of odd nodes with shortest path weights
        complete_graph = nx.Graph()
        for node1, node2 in odd_node_pairs:
            try:
                # Use undirected graph for shortest path
                undirected = self.graph.to_undirected()
                path = nx.shortest_path(undirected, node1, node2, weight='length')
                path_length = nx.shortest_path_length(undirected, node1, node2, weight='length')
                complete_graph.add_edge(node1, node2, weight=path_length, path=path)
            except nx.NetworkXNoPath:
                logger.warning(f"No path found between {node1} and {node2}")
                continue
        
        # Find minimum weight perfect matching
        matching = nx.algorithms.matching.min_weight_matching(complete_graph, weight='weight')
        
        # Extract paths for matched pairs
        matched_paths = []
        for node1, node2 in matching:
            path = complete_graph[node1][node2]['path']
            matched_paths.append((node1, node2, path))
        
        return matched_paths
    
    def _find_euler_circuit(self) -> List[Tuple[int, int]]:
        """
        Find an Euler circuit in the augmented graph.
        
        Returns:
            List of edges forming the Euler circuit
        """
        # Convert to undirected for Eulerian circuit finding
        undirected = self.augmented_graph.to_undirected(as_view=False)
        
        # Ensure graph is connected
        if not nx.is_connected(undirected):
            # Find the largest connected component
            largest_cc = max(nx.connected_components(undirected), key=len)
            undirected = undirected.subgraph(largest_cc).copy()
            logger.warning("Graph not connected, using largest connected component")
        
        # Find Eulerian circuit
        try:
            euler_circuit = list(nx.eulerian_circuit(undirected))
            return euler_circuit
        except:
            logger.warning("Could not find Euler circuit, returning approximation")
            # Return edges in DFS order as approximation
            edges = []
            visited = set()
            
            def dfs(node):
                visited.add(node)
                for neighbor in undirected.neighbors(node):
                    if neighbor not in visited:
                        edges.append((node, neighbor))
                        dfs(neighbor)
            
            start_node = list(undirected.nodes())[0]
            dfs(start_node)
            return edges
    
    def get_total_distance(self) -> float:
        """
        Calculate total distance of the route.
        
        Returns:
            Total distance in meters (or graph units)
        """
        if not self.euler_circuit:
            return 0
        
        total_distance = 0
        for u, v in self.euler_circuit:
            if self.augmented_graph.has_edge(u, v):
                edge_data = self.augmented_graph[u][v]
                if isinstance(edge_data, dict) and 'length' in edge_data:
                    total_distance += edge_data['length']
                else:
                    # Handle multiple edges
                    total_distance += edge_data[0].get('length', 0)
            elif self.augmented_graph.has_edge(v, u):
                edge_data = self.augmented_graph[v][u]
                if isinstance(edge_data, dict) and 'length' in edge_data:
                    total_distance += edge_data['length']
                else:
                    total_distance += edge_data[0].get('length', 0)
        
        return total_distance
    
    def get_route_stats(self) -> Dict:
        """
        Get statistics about the solved route.
        
        Returns:
            Dictionary with route statistics
        """
        if not self.euler_circuit:
            return {}
        
        stats = {
            'total_edges': len(self.euler_circuit),
            'total_distance': self.get_total_distance(),
            'unique_edges': len(set(self.euler_circuit)),
            'repeated_edges': len(self.euler_circuit) - len(set(self.euler_circuit))
        }
        
        # Calculate coverage
        original_edges = self.graph.number_of_edges()
        stats['edge_coverage'] = len(set(self.euler_circuit)) / original_edges * 100
        
        return stats