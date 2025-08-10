import React, { useState } from 'react';
import './ControlPanel.css';

interface ControlPanelProps {
  onPlanRoute: (networkType: string) => void;
  onExport: (format: string) => void;
  onSearchPlace: (placeName: string, networkType: string) => void;
  routeStats?: any;
  areaStats?: any;
  isLoading?: boolean;
  progress?: {
    status: string;
    message: string;
    progress?: number;
  };
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  onPlanRoute,
  onExport,
  onSearchPlace,
  routeStats,
  areaStats,
  isLoading,
  progress,
}) => {
  const [networkType, setNetworkType] = useState('drive');
  const [placeName, setPlaceName] = useState('');

  const handlePlanRoute = () => {
    onPlanRoute(networkType);
  };

  const handleSearchPlace = () => {
    if (placeName.trim()) {
      onSearchPlace(placeName, networkType);
    }
  };

  const formatDistance = (meters: number) => {
    if (meters < 1000) {
      return `${meters.toFixed(0)} m`;
    }
    return `${(meters / 1000).toFixed(2)} km`;
  };

  return (
    <div className="control-panel">
      <h2>StreetView Route Planner</h2>
      
      <div className="section">
        <h3>Region Selection</h3>
        <div className="instructions">
          Use the drawing tools on the map to select a region:
          <ul>
            <li>Rectangle: Draw a bounding box</li>
            <li>Circle: Select area around a point</li>
            <li>Polygon: Draw custom area</li>
          </ul>
        </div>
        
        <div className="place-search">
          <input
            type="text"
            placeholder="Or enter a place name..."
            value={placeName}
            onChange={(e) => setPlaceName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearchPlace()}
          />
          <button onClick={handleSearchPlace} disabled={isLoading}>
            Search Place
          </button>
        </div>
      </div>

      <div className="section">
        <h3>Network Type</h3>
        <select 
          value={networkType} 
          onChange={(e) => setNetworkType(e.target.value)}
          disabled={isLoading}
        >
          <option value="drive">Drive</option>
          <option value="walk">Walk</option>
          <option value="bike">Bike</option>
        </select>
      </div>

      <div className="section">
        <button 
          className="plan-button"
          onClick={handlePlanRoute}
          disabled={isLoading}
        >
          {isLoading ? 'Planning...' : 'Plan Route'}
        </button>
      </div>

      {progress && (
        <div className="progress-section">
          <div className="progress-message">{progress.message}</div>
          {progress.progress !== undefined && (
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${progress.progress}%` }}
              />
            </div>
          )}
        </div>
      )}

      {areaStats && (
        <div className="section stats">
          <h3>Area Statistics</h3>
          <div className="stat-item">
            <span>Nodes:</span> {areaStats.n_nodes}
          </div>
          <div className="stat-item">
            <span>Edges:</span> {areaStats.n_edges}
          </div>
          <div className="stat-item">
            <span>Total Length:</span> {formatDistance(areaStats.total_edge_length)}
          </div>
          <div className="stat-item">
            <span>Is Eulerian:</span> {areaStats.is_eulerian ? 'Yes' : 'No'}
          </div>
        </div>
      )}

      {routeStats && (
        <div className="section stats">
          <h3>Route Statistics</h3>
          <div className="stat-item">
            <span>Total Distance:</span> {formatDistance(routeStats.total_distance)}
          </div>
          <div className="stat-item">
            <span>Unique Edges:</span> {routeStats.unique_edges}
          </div>
          <div className="stat-item">
            <span>Repeated Edges:</span> {routeStats.repeated_edges}
          </div>
          <div className="stat-item">
            <span>Coverage:</span> {routeStats.edge_coverage?.toFixed(1)}%
          </div>
        </div>
      )}

      {routeStats && (
        <div className="section">
          <h3>Export Route</h3>
          <div className="export-buttons">
            <button onClick={() => onExport('gpx')}>Export GPX</button>
            <button onClick={() => onExport('kml')}>Export KML</button>
            <button onClick={() => onExport('geojson')}>Export GeoJSON</button>
            <button onClick={() => onExport('csv')}>Export CSV</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ControlPanel;