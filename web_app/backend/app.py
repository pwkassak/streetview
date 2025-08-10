"""
FastAPI backend for StreetView route planning web application.
"""

import os
import logging

# Configure main app logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'app.log'), mode='a'),
        logging.StreamHandler()
    ],
    force=True
)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from models import (
    BoundingBoxRequest, PointRadiusRequest, PlaceNameRequest,
    RouteResponse, RouteListResponse, RouteProgress, ErrorResponse
)
from route_service import RouteService
import asyncio
import json
import os
import logging
from typing import Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="StreetView Route Planner API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize route service
route_service = RouteService()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_progress(self, client_id: str, progress: RouteProgress):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(progress.dict())

manager = ConnectionManager()


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "StreetView Route Planner API",
        "version": "1.0.0",
        "endpoints": [
            "/api/plan-route/bbox",
            "/api/plan-route/point",
            "/api/plan-route/place",
            "/api/routes",
            "/api/route/{route_id}",
            "/api/export/{route_id}/{format}",
            "/ws"
        ]
    }


@app.post("/api/plan-route/bbox", response_model=RouteResponse)
async def plan_route_bbox(request: BoundingBoxRequest):
    """Plan a route for a bounding box area."""
    logger.info(f"Received bbox route planning request: {request.dict()}")
    try:
        # Create progress callback
        async def progress_callback(data: Dict[str, Any]):
            progress = RouteProgress(**data)
            # Send to all connected WebSocket clients
            for client_id in list(manager.active_connections.keys()):
                await manager.send_progress(client_id, progress)
        
        # Plan route
        route_id = await route_service.plan_route_bbox(
            request.north,
            request.south,
            request.east,
            request.west,
            request.network_type,
            progress_callback
        )
        
        # Get route data
        route = route_service.get_route(route_id)
        
        return RouteResponse(
            route_id=route_id,
            status=route['status'],
            created_at=route['created_at'],
            area_stats=route['area_stats'],
            route_stats=route.get('route_stats'),
            geojson=route.get('geojson')
        )
        
    except Exception as e:
        logger.error(f"Error planning route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plan-route/point", response_model=RouteResponse)
async def plan_route_point(request: PointRadiusRequest):
    """Plan a route around a point with radius."""
    try:
        async def progress_callback(data: Dict[str, Any]):
            progress = RouteProgress(**data)
            for client_id in list(manager.active_connections.keys()):
                await manager.send_progress(client_id, progress)
        
        route_id = await route_service.plan_route_point(
            request.latitude,
            request.longitude,
            request.radius_meters,
            request.network_type,
            progress_callback
        )
        
        route = route_service.get_route(route_id)
        
        return RouteResponse(
            route_id=route_id,
            status=route['status'],
            created_at=route['created_at'],
            area_stats=route['area_stats'],
            route_stats=route.get('route_stats'),
            geojson=route.get('geojson')
        )
        
    except Exception as e:
        logger.error(f"Error planning route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plan-route/place", response_model=RouteResponse)
async def plan_route_place(request: PlaceNameRequest):
    """Plan a route for a named place."""
    try:
        async def progress_callback(data: Dict[str, Any]):
            progress = RouteProgress(**data)
            for client_id in list(manager.active_connections.keys()):
                await manager.send_progress(client_id, progress)
        
        route_id = await route_service.plan_route_place(
            request.place_name,
            request.network_type,
            progress_callback
        )
        
        route = route_service.get_route(route_id)
        
        return RouteResponse(
            route_id=route_id,
            status=route['status'],
            created_at=route['created_at'],
            area_stats=route['area_stats'],
            route_stats=route.get('route_stats'),
            geojson=route.get('geojson')
        )
        
    except Exception as e:
        logger.error(f"Error planning route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/routes", response_model=RouteListResponse)
async def list_routes():
    """List all available routes."""
    routes = route_service.list_routes()
    return RouteListResponse(routes=routes)


@app.get("/api/route/{route_id}", response_model=RouteResponse)
async def get_route(route_id: str):
    """Get route details by ID."""
    route = route_service.get_route(route_id)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return RouteResponse(
        route_id=route_id,
        status=route['status'],
        created_at=route['created_at'],
        area_stats=route['area_stats'],
        route_stats=route.get('route_stats'),
        geojson=route.get('geojson')
    )


@app.get("/api/export/{route_id}/{format}")
async def export_route(route_id: str, format: str):
    """Export route to specified format."""
    if format not in ['gpx', 'kml', 'geojson', 'csv']:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    file_path = await route_service.export_route(route_id, format)
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export not found")
    
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=f"route_{route_id}.{format}"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    client_id = str(datetime.now().timestamp())
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or handle specific commands if needed
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)