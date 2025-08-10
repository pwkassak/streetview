import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import ControlPanel from './components/ControlPanel';
import api, { RouteResponse, RouteProgress } from './services/api';
import './App.css';

function App() {
  const [selectedRegion, setSelectedRegion] = useState<any>(null);
  const [currentRoute, setCurrentRoute] = useState<RouteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<RouteProgress | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket for progress updates
    const websocket = api.connectWebSocket((progress) => {
      setProgress(progress);
      if (progress.status === 'completed' || progress.status === 'error') {
        setTimeout(() => setProgress(null), 3000);
      }
    });
    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  const handleRegionSelect = (region: any) => {
    setSelectedRegion(region);
    console.log('Region selected:', region);
  };

  const handlePlanRoute = async (networkType: string) => {
    if (!selectedRegion) {
      alert('Please select a region on the map first');
      return;
    }

    setIsLoading(true);
    setProgress({ status: 'loading', message: 'Starting route planning...' });

    try {
      let response: RouteResponse;
      
      if (selectedRegion.type === 'bbox') {
        response = await api.planRouteBbox({
          north: selectedRegion.north,
          south: selectedRegion.south,
          east: selectedRegion.east,
          west: selectedRegion.west,
        }, networkType);
      } else if (selectedRegion.type === 'point') {
        response = await api.planRoutePoint({
          latitude: selectedRegion.latitude,
          longitude: selectedRegion.longitude,
          radius_meters: selectedRegion.radius_meters,
        }, networkType);
      } else {
        throw new Error('Unknown region type');
      }

      setCurrentRoute(response);
      console.log('Route planned:', response);
    } catch (error) {
      console.error('Error planning route:', error);
      setProgress({ 
        status: 'error', 
        message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchPlace = async (placeName: string, networkType: string) => {
    setIsLoading(true);
    setProgress({ status: 'loading', message: `Searching for ${placeName}...` });

    try {
      const response = await api.planRoutePlace(placeName, networkType);
      setCurrentRoute(response);
      console.log('Route planned for place:', response);
    } catch (error) {
      console.error('Error planning route for place:', error);
      setProgress({ 
        status: 'error', 
        message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async (format: string) => {
    if (!currentRoute) {
      alert('No route to export');
      return;
    }

    try {
      await api.exportRoute(currentRoute.route_id, format);
    } catch (error) {
      console.error('Error exporting route:', error);
      alert('Failed to export route');
    }
  };

  return (
    <div className="app">
      <div className="map-container">
        <MapView
          onRegionSelect={handleRegionSelect}
          routeData={currentRoute}
        />
      </div>
      
      <ControlPanel
        onPlanRoute={handlePlanRoute}
        onExport={handleExport}
        onSearchPlace={handleSearchPlace}
        routeStats={currentRoute?.route_stats}
        areaStats={currentRoute?.area_stats}
        isLoading={isLoading}
        progress={progress}
      />
    </div>
  );
}

export default App;