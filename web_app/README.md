# StreetView Route Planner Web App

A lightweight web application for selecting regions on a map and planning optimal routes that cover all streets in the selected area.

## Features

- **Interactive Map Interface**: Select regions using drawing tools (rectangle, circle, polygon)
- **Place Search**: Search and plan routes by place name
- **Real-time Progress**: WebSocket updates during route calculation
- **Route Visualization**: Display calculated routes on the map with start/end markers
- **Statistics Display**: View area and route statistics
- **Export Options**: Download routes in GPX, KML, GeoJSON, or CSV formats
- **Network Types**: Support for drive, walk, and bike routing

## Setup

### Backend (FastAPI)

1. Navigate to the backend directory:
```bash
cd streetview/web_app/backend
```

2. Install dependencies:
```bash
conda activate streetview310
pip install -r requirements.txt
```

3. Start the backend server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

### Frontend (React + TypeScript)

1. Navigate to the frontend directory:
```bash
cd streetview/web_app/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The web app will open at `http://localhost:3000`

## Usage

1. **Select a Region**:
   - Use the rectangle tool to draw a bounding box
   - Use the circle tool to select an area around a point
   - Use the polygon tool to draw a custom area
   - Or enter a place name in the search box

2. **Choose Network Type**:
   - Drive: For vehicle routing
   - Walk: For pedestrian paths
   - Bike: For cycling routes

3. **Plan Route**:
   - Click "Plan Route" to calculate the optimal path
   - Watch real-time progress updates
   - View statistics when complete

4. **Export Results**:
   - Download the route in various formats
   - GPX for GPS devices
   - KML for Google Earth
   - GeoJSON for GIS applications
   - CSV for data analysis

## API Endpoints

- `POST /api/plan-route/bbox` - Plan route for bounding box
- `POST /api/plan-route/point` - Plan route around point
- `POST /api/plan-route/place` - Plan route for place name
- `GET /api/routes` - List all routes
- `GET /api/route/{id}` - Get route details
- `GET /api/export/{id}/{format}` - Export route
- `WebSocket /ws` - Real-time progress updates

## Technologies

- **Backend**: FastAPI, Python 3.10, OSMnx, NetworkX
- **Frontend**: React, TypeScript, Leaflet, React-Leaflet
- **Real-time**: WebSockets for progress updates