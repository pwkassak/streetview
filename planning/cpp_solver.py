"""
Optimized Chinese Postman Problem solver using the postman_problems library.
"""

import networkx as nx
import pandas as pd
import logging
from typing import List, Tuple, Dict
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CPPSolver:
    """Solves the Chinese Postman Problem using the postman_problems library."""
    
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
        Solve the Chinese Postman Problem using the postman_problems library.
        
        Returns:
            List of edges representing the optimal tour
        """
        logger.info("Starting optimized Chinese Postman Problem solution")
        
        # Convert graph to edge list DataFrame
        edge_list = self._graph_to_edgelist()
        
        # Create temporary CSV file for the solver
        # (The library requires a file path, we'll use a temp file)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            edge_list.to_csv(f, index=False)
        
        try:
            # Import here to avoid issues if not installed
            from postman_problems.solver import cpp
            
            # Solve the CPP
            logger.info(f"Solving CPP with {len(edge_list)} edges...")
            circuit, augmented_graph = cpp(temp_path, edge_weight='distance')
            
            # Store the augmented graph for stats calculation
            self.augmented_graph = augmented_graph
            
            # Convert circuit to list of edge tuples
            # The circuit contains edge data with 'node_from' and 'node_to'
            # Convert node IDs back to integers if they were originally integers
            try:
                # Check if original graph has integer node IDs
                sample_node = next(iter(self.graph.nodes()))
                if isinstance(sample_node, int):
                    self.euler_circuit = [(int(edge[0]), int(edge[1])) for edge in circuit]
                else:
                    self.euler_circuit = [(edge[0], edge[1]) for edge in circuit]
            except (ValueError, StopIteration):
                # Fallback to string IDs if conversion fails
                self.euler_circuit = [(edge[0], edge[1]) for edge in circuit]
            logger.info(f"Found Euler circuit with {len(self.euler_circuit)} edges")
            
            return self.euler_circuit
            
        except Exception as e:
            logger.error(f"Error solving CPP: {e}")
            raise
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _graph_to_edgelist(self) -> pd.DataFrame:
        """
        Convert NetworkX graph to edge list DataFrame format expected by postman_problems.
        
        Returns:
            DataFrame with columns: node_from, node_to, distance, and other edge attributes
        """
        edges = []
        
        # Handle MultiDiGraph - may have multiple edges between nodes
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            edge_data = {
                'node_from': u,
                'node_to': v,
                'distance': data.get('length', 1.0),  # Use 'distance' column name expected by library
                'length': data.get('length', 1.0)  # Keep length for compatibility
            }
            
            # Add other relevant attributes
            for attr in ['name', 'highway', 'oneway']:
                if attr in data:
                    edge_data[attr] = data[attr]
            
            edges.append(edge_data)
        
        df = pd.DataFrame(edges)
        logger.info(f"Converted graph to edge list with {len(df)} edges")
        
        return df
    
    def get_route_stats(self) -> dict:
        """
        Get statistics about the planned route.
        
        Returns:
            Dictionary with route statistics
        """
        if not self.euler_circuit:
            return {}
        
        # Calculate total distance using the augmented graph from postman_problems
        total_distance = 0
        edge_counts = {}
        
        # Use augmented graph if available for accurate distance
        graph_to_use = self.augmented_graph if self.augmented_graph else self.graph
        
        for u, v in self.euler_circuit:
            # Get edge data - try with original node IDs first, then strings
            edge_length = 0
            
            # For augmented graph from postman_problems, node IDs might be strings
            u_str, v_str = str(u), str(v)
            
            # Try original IDs first (for our graph), then string IDs (for augmented)
            for u_try, v_try in [(u, v), (u_str, v_str)]:
                if graph_to_use.has_edge(u_try, v_try):
                    edge_data = graph_to_use[u_try][v_try]
                    # Handle different edge data structures
                    if isinstance(edge_data, dict):
                        edge_length = edge_data.get('distance', edge_data.get('length', 0))
                    else:
                        # For MultiGraph, get the first edge
                        for key in edge_data:
                            edge_length = edge_data[key].get('distance', edge_data[key].get('length', 0))
                            break
                    break
                elif graph_to_use.has_edge(v_try, u_try):
                    edge_data = graph_to_use[v_try][u_try]
                    if isinstance(edge_data, dict):
                        edge_length = edge_data.get('distance', edge_data.get('length', 0))
                    else:
                        for key in edge_data:
                            edge_length = edge_data[key].get('distance', edge_data[key].get('length', 0))
                            break
                    break
            
            total_distance += edge_length
            
            # Count edge traversals
            edge_key = tuple(sorted([u, v]))
            edge_counts[edge_key] = edge_counts.get(edge_key, 0) + 1
        
        # Count edges traversed more than once
        repeated_edges = sum(1 for count in edge_counts.values() if count > 1)
        total_repetitions = sum(count - 1 for count in edge_counts.values() if count > 1)
        
        # Calculate original graph stats for coverage
        original_edges = self.graph.number_of_edges()
        edge_coverage = (len(edge_counts) / original_edges * 100) if original_edges > 0 else 0
        
        return {
            'total_edges': len(self.euler_circuit),
            'unique_edges': len(edge_counts),
            'repeated_edges': repeated_edges,
            'total_repetitions': total_repetitions,
            'total_distance': round(total_distance, 2),  # Keep as total_distance for compatibility
            'total_distance_m': round(total_distance, 2),
            'total_distance_km': round(total_distance / 1000, 2),
            'edge_coverage': round(edge_coverage, 1)
        }