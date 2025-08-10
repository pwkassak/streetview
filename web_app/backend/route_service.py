"""
Service layer for route planning, wrapping the existing RoutePlanner.
"""

import sys
import os

# Get absolute path to planning directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(backend_dir))
planning_dir = os.path.join(project_root, 'planning')
sys.path.insert(0, planning_dir)

from route_planner import RoutePlanner
from typing import Dict, Any, Optional, List, Tuple
import uuid
from datetime import datetime
import json
import asyncio
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging to file
log_file = os.path.join(log_dir, 'route_service.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)


class RouteService:
    """Service for managing route planning operations."""
    
    def __init__(self):
        self.routes = {}  # In-memory storage for routes
        self.active_planners = {}  # Track active planning sessions
        self.backend_dir = backend_dir  # Store backend directory for output paths
        
    async def plan_route_bbox(self, north: float, south: float, east: float, west: float,
                              network_type: str = 'drive',
                              progress_callback=None) -> str:
        """
        Plan a route for a bounding box area.
        
        Args:
            north: Northern latitude
            south: Southern latitude
            east: Eastern longitude
            west: Western longitude
            network_type: Network type ('drive', 'walk', 'bike')
            progress_callback: Optional async callback for progress updates
            
        Returns:
            Route ID
        """
        route_id = str(uuid.uuid4())
        
        logger.info(f"[{route_id}] ===== Starting route planning for bbox =====")
        logger.info(f"[{route_id}] Bbox: N={north:.6f}, S={south:.6f}, E={east:.6f}, W={west:.6f}")
        logger.info(f"[{route_id}] Network type: {network_type}")
        
        try:
            # Initialize planner
            logger.info(f"[{route_id}] Creating RoutePlanner instance...")
            planner = RoutePlanner(network_type)
            self.active_planners[route_id] = planner
            logger.info(f"[{route_id}] RoutePlanner created successfully")
            
            # Progress: Loading area
            if progress_callback:
                await progress_callback({
                    'status': 'loading',
                    'message': 'Loading street network from OpenStreetMap...',
                    'progress': 10
                })
            
            # Load area
            start_time = datetime.now()
            logger.info(f"[{route_id}] Starting OSM data download...")
            logger.info(f"[{route_id}] Calling planner.load_area_by_bbox with params: north={north}, south={south}, east={east}, west={west}")
            
            await asyncio.to_thread(planner.load_area_by_bbox, north, south, east, west)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{route_id}] Area loaded successfully in {duration:.2f} seconds")
            
            # Get area statistics
            logger.info(f"[{route_id}] Getting area statistics...")
            area_stats = planner.get_area_stats()
            logger.info(f"[{route_id}] Area stats: nodes={area_stats.get('n_nodes')}, edges={area_stats.get('n_edges')}")
            
            if progress_callback:
                await progress_callback({
                    'status': 'planning',
                    'message': f'Planning route for {area_stats["n_nodes"]} nodes and {area_stats["n_edges"]} edges...',
                    'progress': 40,
                    'details': area_stats
                })
            
            # Plan route
            start_time = datetime.now()
            logger.info(f"[{route_id}] Starting route planning algorithm...")
            route = await asyncio.to_thread(planner.plan_route)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{route_id}] Route planned successfully in {duration:.2f} seconds, contains {len(route)} edges")
            
            # Get route statistics
            logger.info(f"[{route_id}] Getting route statistics...")
            route_stats = planner.get_route_stats()
            logger.info(f"[{route_id}] Route stats: distance={route_stats.get('total_distance'):.0f}m, coverage={route_stats.get('edge_coverage'):.1f}%")
            
            if progress_callback:
                await progress_callback({
                    'status': 'exporting',
                    'message': 'Generating route visualization...',
                    'progress': 70
                })
            
            # Export to GeoJSON for visualization
            output_dir = os.path.join(self.backend_dir, "output", "routes", route_id)
            os.makedirs(output_dir, exist_ok=True)
            
            output_files = await asyncio.to_thread(
                planner.export_route,
                output_dir,
                ['geojson'],
                'route'
            )
            
            # Load GeoJSON for immediate visualization
            geojson_path = output_files.get('geojson')
            geojson_data = None
            if geojson_path and os.path.exists(geojson_path):
                with open(geojson_path, 'r') as f:
                    geojson_data = json.load(f)
            
            # Store route information
            self.routes[route_id] = {
                'route_id': route_id,
                'status': 'completed',
                'created_at': datetime.now(),
                'area_stats': area_stats,
                'route_stats': route_stats,
                'planner': planner,
                'output_dir': output_dir,
                'geojson': geojson_data,
                'network_type': network_type,
                'region': {
                    'type': 'bbox',
                    'north': north,
                    'south': south,
                    'east': east,
                    'west': west
                }
            }
            
            if progress_callback:
                await progress_callback({
                    'status': 'completed',
                    'message': 'Route planning completed successfully!',
                    'progress': 100,
                    'details': route_stats
                })
            
            return route_id
            
        except Exception as e:
            import traceback
            logger.error(f"Error planning route: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if progress_callback:
                await progress_callback({
                    'status': 'error',
                    'message': f'Error: {str(e)}',
                    'progress': 0
                })
            raise
        finally:
            # Clean up active planner
            if route_id in self.active_planners:
                del self.active_planners[route_id]
    
    async def plan_route_point(self, lat: float, lon: float, radius_m: float,
                               network_type: str = 'drive',
                               progress_callback=None) -> str:
        """
        Plan a route around a point with radius.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_m: Radius in meters
            network_type: Network type
            progress_callback: Optional async callback for progress updates
            
        Returns:
            Route ID
        """
        route_id = str(uuid.uuid4())
        
        try:
            planner = RoutePlanner(network_type)
            self.active_planners[route_id] = planner
            
            if progress_callback:
                await progress_callback({
                    'status': 'loading',
                    'message': f'Loading street network within {radius_m}m of point...',
                    'progress': 10
                })
            
            # Load area
            await asyncio.to_thread(planner.load_area_by_point, lat, lon, radius_m)
            
            # Continue with same flow as bbox
            area_stats = planner.get_area_stats()
            
            if progress_callback:
                await progress_callback({
                    'status': 'planning',
                    'message': f'Planning route for {area_stats["n_nodes"]} nodes...',
                    'progress': 40,
                    'details': area_stats
                })
            
            route = await asyncio.to_thread(planner.plan_route)
            route_stats = planner.get_route_stats()
            
            if progress_callback:
                await progress_callback({
                    'status': 'exporting',
                    'message': 'Generating route visualization...',
                    'progress': 70
                })
            
            output_dir = os.path.join(self.backend_dir, "output", "routes", route_id)
            os.makedirs(output_dir, exist_ok=True)
            
            output_files = await asyncio.to_thread(
                planner.export_route,
                output_dir,
                ['geojson'],
                'route'
            )
            
            geojson_path = output_files.get('geojson')
            geojson_data = None
            if geojson_path and os.path.exists(geojson_path):
                with open(geojson_path, 'r') as f:
                    geojson_data = json.load(f)
            
            self.routes[route_id] = {
                'route_id': route_id,
                'status': 'completed',
                'created_at': datetime.now(),
                'area_stats': area_stats,
                'route_stats': route_stats,
                'planner': planner,
                'output_dir': output_dir,
                'geojson': geojson_data,
                'network_type': network_type,
                'region': {
                    'type': 'point',
                    'latitude': lat,
                    'longitude': lon,
                    'radius_meters': radius_m
                }
            }
            
            if progress_callback:
                await progress_callback({
                    'status': 'completed',
                    'message': 'Route planning completed!',
                    'progress': 100,
                    'details': route_stats
                })
            
            return route_id
            
        except Exception as e:
            import traceback
            logger.error(f"Error planning route: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if progress_callback:
                await progress_callback({
                    'status': 'error',
                    'message': f'Error: {str(e)}',
                    'progress': 0
                })
            raise
        finally:
            if route_id in self.active_planners:
                del self.active_planners[route_id]
    
    async def plan_route_place(self, place_name: str,
                               network_type: str = 'drive',
                               progress_callback=None) -> str:
        """
        Plan a route for a named place.
        
        Args:
            place_name: Name of the place
            network_type: Network type
            progress_callback: Optional async callback for progress updates
            
        Returns:
            Route ID
        """
        route_id = str(uuid.uuid4())
        
        try:
            planner = RoutePlanner(network_type)
            self.active_planners[route_id] = planner
            
            if progress_callback:
                await progress_callback({
                    'status': 'loading',
                    'message': f'Loading street network for {place_name}...',
                    'progress': 10
                })
            
            # Load area
            await asyncio.to_thread(planner.load_area_by_place, place_name)
            
            # Continue with same flow
            area_stats = planner.get_area_stats()
            
            if progress_callback:
                await progress_callback({
                    'status': 'planning',
                    'message': f'Planning route for {area_stats["n_nodes"]} nodes...',
                    'progress': 40,
                    'details': area_stats
                })
            
            route = await asyncio.to_thread(planner.plan_route)
            route_stats = planner.get_route_stats()
            
            if progress_callback:
                await progress_callback({
                    'status': 'exporting',
                    'message': 'Generating route visualization...',
                    'progress': 70
                })
            
            output_dir = os.path.join(self.backend_dir, "output", "routes", route_id)
            os.makedirs(output_dir, exist_ok=True)
            
            output_files = await asyncio.to_thread(
                planner.export_route,
                output_dir,
                ['geojson'],
                'route'
            )
            
            geojson_path = output_files.get('geojson')
            geojson_data = None
            if geojson_path and os.path.exists(geojson_path):
                with open(geojson_path, 'r') as f:
                    geojson_data = json.load(f)
            
            self.routes[route_id] = {
                'route_id': route_id,
                'status': 'completed',
                'created_at': datetime.now(),
                'area_stats': area_stats,
                'route_stats': route_stats,
                'planner': planner,
                'output_dir': output_dir,
                'geojson': geojson_data,
                'network_type': network_type,
                'region': {
                    'type': 'place',
                    'place_name': place_name
                }
            }
            
            if progress_callback:
                await progress_callback({
                    'status': 'completed',
                    'message': 'Route planning completed!',
                    'progress': 100,
                    'details': route_stats
                })
            
            return route_id
            
        except Exception as e:
            import traceback
            logger.error(f"Error planning route: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if progress_callback:
                await progress_callback({
                    'status': 'error',
                    'message': f'Error: {str(e)}',
                    'progress': 0
                })
            raise
        finally:
            if route_id in self.active_planners:
                del self.active_planners[route_id]
    
    def get_route(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Get route information by ID."""
        return self.routes.get(route_id)
    
    def list_routes(self) -> List[Dict[str, Any]]:
        """List all available routes."""
        return [
            {
                'route_id': r['route_id'],
                'status': r['status'],
                'created_at': r['created_at'].isoformat(),
                'network_type': r.get('network_type', 'drive'),
                'region': r.get('region', {}),
                'stats': {
                    'nodes': r['area_stats'].get('n_nodes', 0),
                    'edges': r['area_stats'].get('n_edges', 0),
                    'total_distance': r['route_stats'].get('total_distance', 0) if r.get('route_stats') else 0
                }
            }
            for r in self.routes.values()
        ]
    
    async def export_route(self, route_id: str, format: str) -> Optional[str]:
        """
        Export route to specified format.
        
        Args:
            route_id: Route ID
            format: Export format ('gpx', 'kml', 'geojson', 'csv')
            
        Returns:
            Path to exported file
        """
        route = self.routes.get(route_id)
        if not route or 'planner' not in route:
            return None
        
        planner = route['planner']
        output_dir = route['output_dir']
        
        # Export the requested format
        output_files = await asyncio.to_thread(
            planner.export_route,
            output_dir,
            [format],
            'route'
        )
        
        return output_files.get(format)