import { useState, useEffect, useCallback } from 'react';
import MapView from './components/MapView';
import ControlPanel from './components/ControlPanel';
import RoutePlayer from './components/RoutePlayer';
import api, { RouteResponse, RouteProgress } from './services/api';
import './App.css';

function App() {
  const [selectedRegion, setSelectedRegion] = useState<any>(null);
  const [currentRoute, setCurrentRoute] = useState<RouteResponse | null>(null);
  const [routeSegments, setRouteSegments] = useState<any>(null);
  const [currentSegment, setCurrentSegment] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showFullRoute, setShowFullRoute] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<RouteProgress | null>(null);
  const [, setWs] = useState<WebSocket | null>(null);

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
      
      // Load segments for interactive visualization
      try {
        const segments = await api.getRouteSegments(response.route_id);
        setRouteSegments(segments);
        setCurrentSegment(0);
        setShowFullRoute(false);
        console.log('Route segments loaded:', segments);
      } catch (error) {
        console.error('Error loading route segments:', error);
        // Fall back to showing full route
        setShowFullRoute(true);
      }
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
      
      // Load segments for interactive visualization
      try {
        const segments = await api.getRouteSegments(response.route_id);
        setRouteSegments(segments);
        setCurrentSegment(0);
        setShowFullRoute(false);
        console.log('Route segments loaded:', segments);
      } catch (error) {
        console.error('Error loading route segments:', error);
        // Fall back to showing full route
        setShowFullRoute(true);
      }
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

  const handlePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  const handleSegmentChange = useCallback((segment: number) => {
    setCurrentSegment(segment);
  }, []);

  const handleSpeedChange = useCallback((speed: number) => {
    setPlaybackSpeed(speed);
  }, []);

  const handleReset = useCallback(() => {
    setCurrentSegment(0);
    setIsPlaying(false);
  }, []);

  const toggleRouteView = useCallback(() => {
    setShowFullRoute(prev => !prev);
  }, []);

  return (
    <div className="app">
      <div className="map-container">
        <MapView
          onRegionSelect={handleRegionSelect}
          routeData={currentRoute}
          routeSegments={routeSegments}
          currentSegment={currentSegment}
          showFullRoute={showFullRoute}
        />
      </div>
      
      <ControlPanel
        onPlanRoute={handlePlanRoute}
        onExport={handleExport}
        onSearchPlace={handleSearchPlace}
        routeStats={currentRoute?.route_stats}
        areaStats={currentRoute?.area_stats}
        isLoading={isLoading}
        progress={progress || undefined}
      />
      
      {routeSegments && (
        <>
          <RoutePlayer
            totalSegments={routeSegments.features?.length || 0}
            currentSegment={currentSegment}
            isPlaying={isPlaying}
            playbackSpeed={playbackSpeed}
            onSegmentChange={handleSegmentChange}
            onPlayPause={handlePlayPause}
            onSpeedChange={handleSpeedChange}
            onReset={handleReset}
            maxTraversals={routeSegments.properties?.max_traversals || 1}
          />
          
          {/* Toggle button for full route view */}
          <button
            onClick={toggleRouteView}
            style={{
              position: 'absolute',
              top: '70px',
              right: '340px',
              zIndex: 1000,
              padding: '8px 16px',
              background: showFullRoute ? '#FF9500' : '#0066CC',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              boxShadow: '0 2px 6px rgba(0,0,0,0.2)'
            }}
          >
            {showFullRoute ? 'Show Progress Mode' : 'Show Full Route'}
          </button>
        </>
      )}
    </div>
  );
}

export default App;