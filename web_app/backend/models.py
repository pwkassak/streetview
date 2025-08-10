"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class BoundingBoxRequest(BaseModel):
    """Request model for bounding box region selection."""
    north: float
    south: float
    east: float
    west: float
    network_type: Literal['drive', 'walk', 'bike'] = 'drive'


class PointRadiusRequest(BaseModel):
    """Request model for point + radius region selection."""
    latitude: float
    longitude: float
    radius_meters: float = 1000
    network_type: Literal['drive', 'walk', 'bike'] = 'drive'


class PlaceNameRequest(BaseModel):
    """Request model for place name region selection."""
    place_name: str
    network_type: Literal['drive', 'walk', 'bike'] = 'drive'


class RouteProgress(BaseModel):
    """WebSocket message for route planning progress."""
    status: Literal['loading', 'planning', 'exporting', 'completed', 'error']
    message: str
    progress: Optional[int] = None  # Percentage 0-100
    details: Optional[Dict[str, Any]] = None


class RouteResponse(BaseModel):
    """Response model for route planning results."""
    route_id: str
    status: str
    created_at: datetime
    area_stats: Dict[str, Any]
    route_stats: Optional[Dict[str, Any]] = None
    available_formats: List[str] = ['gpx', 'kml', 'geojson', 'csv']
    geojson: Optional[Dict[str, Any]] = None  # For map visualization


class RouteListResponse(BaseModel):
    """Response model for listing available routes."""
    routes: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    details: Optional[str] = None