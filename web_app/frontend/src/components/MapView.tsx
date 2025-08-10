import React, { useState, useCallback } from 'react';
import { MapContainer, TileLayer, Rectangle, Circle, Polygon, Polyline, Marker, Popup, useMapEvents } from 'react-leaflet';
import L, { LatLng } from 'leaflet';
import DrawingToolbar, { DrawingMode } from './DrawingToolbar';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface MapViewProps {
  onRegionSelect: (region: any) => void;
  routeData?: any;
  center?: [number, number];
  zoom?: number;
}

interface DrawnShape {
  type: 'rectangle' | 'circle' | 'polygon';
  data: any;
}

// Component for handling map clicks during drawing
const DrawingHandler: React.FC<{
  mode: DrawingMode;
  onShapeComplete: (shape: DrawnShape) => void;
}> = ({ mode, onShapeComplete }) => {
  const [rectangleCorners, setRectangleCorners] = useState<LatLng[]>([]);
  const [circleCenter, setCircleCenter] = useState<LatLng | null>(null);
  const [polygonPoints, setPolygonPoints] = useState<LatLng[]>([]);

  useMapEvents({
    click(e) {
      if (mode === 'rectangle') {
        if (rectangleCorners.length === 0) {
          setRectangleCorners([e.latlng]);
        } else {
          const bounds = L.latLngBounds([rectangleCorners[0], e.latlng]);
          onShapeComplete({
            type: 'rectangle',
            data: {
              bounds: [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]]
            }
          });
          setRectangleCorners([]);
        }
      } else if (mode === 'circle') {
        if (!circleCenter) {
          setCircleCenter(e.latlng);
        } else {
          const radius = circleCenter.distanceTo(e.latlng);
          onShapeComplete({
            type: 'circle',
            data: {
              center: [circleCenter.lat, circleCenter.lng],
              radius: radius
            }
          });
          setCircleCenter(null);
        }
      } else if (mode === 'polygon') {
        setPolygonPoints([...polygonPoints, e.latlng]);
      }
    },
    dblclick(e) {
      if (mode === 'polygon' && polygonPoints.length >= 3) {
        L.DomEvent.stop(e);
        onShapeComplete({
          type: 'polygon',
          data: {
            positions: polygonPoints.map(p => [p.lat, p.lng])
          }
        });
        setPolygonPoints([]);
      }
    }
  });

  // Render temporary shapes while drawing
  return (
    <>
      {rectangleCorners.length === 1 && (
        <Marker position={rectangleCorners[0]}>
          <Popup>Click to set opposite corner</Popup>
        </Marker>
      )}
      {circleCenter && (
        <Marker position={circleCenter}>
          <Popup>Click to set radius</Popup>
        </Marker>
      )}
      {polygonPoints.length > 0 && (
        <>
          {polygonPoints.map((point, idx) => (
            <Circle
              key={idx}
              center={point}
              radius={50}
              pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.5 }}
            />
          ))}
          {polygonPoints.length > 1 && (
            <Polyline
              positions={polygonPoints}
              pathOptions={{ color: 'blue', dashArray: '5, 10' }}
            />
          )}
        </>
      )}
    </>
  );
};

const MapView: React.FC<MapViewProps> = ({ 
  onRegionSelect, 
  routeData,
  center = [42.3360, -71.2092], // Default to Newton, MA
  zoom = 13 
}) => {
  const [drawingMode, setDrawingMode] = useState<DrawingMode>('none');
  const [drawnShapes, setDrawnShapes] = useState<DrawnShape[]>([]);

  const handleShapeComplete = useCallback((shape: DrawnShape) => {
    setDrawnShapes([shape]); // Replace previous shape
    setDrawingMode('none');

    // Convert shape to region selection format
    if (shape.type === 'rectangle') {
      const bounds = shape.data.bounds;
      onRegionSelect({
        type: 'bbox',
        north: bounds[1][0],
        south: bounds[0][0],
        east: bounds[1][1],
        west: bounds[0][1],
      });
    } else if (shape.type === 'circle') {
      onRegionSelect({
        type: 'point',
        latitude: shape.data.center[0],
        longitude: shape.data.center[1],
        radius_meters: shape.data.radius,
      });
    } else if (shape.type === 'polygon') {
      // Convert polygon to bounding box
      const lats = shape.data.positions.map((p: number[]) => p[0]);
      const lngs = shape.data.positions.map((p: number[]) => p[1]);
      onRegionSelect({
        type: 'bbox',
        north: Math.max(...lats),
        south: Math.min(...lats),
        east: Math.max(...lngs),
        west: Math.min(...lngs),
      });
    }
  }, [onRegionSelect]);

  const handleClear = useCallback(() => {
    setDrawnShapes([]);
    setDrawingMode('none');
  }, []);

  const renderRoute = () => {
    if (!routeData?.geojson?.features?.[0]?.geometry?.coordinates) {
      return null;
    }

    const coordinates = routeData.geojson.features[0].geometry.coordinates;
    const positions: [number, number][] = coordinates.map((coord: number[]) => [coord[1], coord[0]]);

    return (
      <>
        <Polyline 
          positions={positions}
          pathOptions={{ color: 'blue', weight: 3, opacity: 0.8 }}
        />
        {positions.length > 0 && (
          <>
            <Marker position={positions[0]}>
              <Popup>Start Point</Popup>
            </Marker>
            <Marker position={positions[positions.length - 1]}>
              <Popup>End Point</Popup>
            </Marker>
          </>
        )}
      </>
    );
  };

  const renderDrawnShapes = () => {
    return drawnShapes.map((shape, idx) => {
      if (shape.type === 'rectangle') {
        return (
          <Rectangle
            key={`rect-${idx}`}
            bounds={shape.data.bounds}
            pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.2 }}
          />
        );
      } else if (shape.type === 'circle') {
        return (
          <Circle
            key={`circle-${idx}`}
            center={shape.data.center}
            radius={shape.data.radius}
            pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.2 }}
          />
        );
      } else if (shape.type === 'polygon') {
        return (
          <Polygon
            key={`poly-${idx}`}
            positions={shape.data.positions}
            pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.2 }}
          />
        );
      }
      return null;
    });
  };

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        doubleClickZoom={drawingMode !== 'polygon'}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        <DrawingHandler mode={drawingMode} onShapeComplete={handleShapeComplete} />
        {renderDrawnShapes()}
        {renderRoute()}
      </MapContainer>
      
      <DrawingToolbar
        mode={drawingMode}
        onModeChange={setDrawingMode}
        onClear={handleClear}
      />
      
      {drawingMode !== 'none' && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'white',
          padding: '8px 16px',
          borderRadius: '4px',
          boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
          zIndex: 1000,
          fontSize: '14px'
        }}>
          {drawingMode === 'rectangle' && 'Click two corners to draw a rectangle'}
          {drawingMode === 'circle' && 'Click center, then click to set radius'}
          {drawingMode === 'polygon' && 'Click to add points, double-click to finish'}
        </div>
      )}
    </div>
  );
};

export default MapView;