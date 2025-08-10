import axios from 'axios';

const API_BASE_URL = '/api';

export interface BoundingBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface PointRadius {
  latitude: number;
  longitude: number;
  radius_meters: number;
}

export interface RouteResponse {
  route_id: string;
  status: string;
  created_at: string;
  area_stats: {
    n_nodes: number;
    n_edges: number;
    total_edge_length: number;
    is_eulerian: boolean;
  };
  route_stats?: {
    total_distance: number;
    unique_edges: number;
    repeated_edges: number;
    edge_coverage: number;
  };
  geojson?: any;
}

export interface RouteProgress {
  status: 'loading' | 'planning' | 'exporting' | 'completed' | 'error';
  message: string;
  progress?: number;
  details?: any;
}

class RouteAPI {
  async planRouteBbox(bbox: BoundingBox, networkType: string = 'drive'): Promise<RouteResponse> {
    const response = await axios.post(`${API_BASE_URL}/plan-route/bbox`, {
      ...bbox,
      network_type: networkType,
    });
    return response.data;
  }

  async planRoutePoint(point: PointRadius, networkType: string = 'drive'): Promise<RouteResponse> {
    const response = await axios.post(`${API_BASE_URL}/plan-route/point`, {
      ...point,
      network_type: networkType,
    });
    return response.data;
  }

  async planRoutePlace(placeName: string, networkType: string = 'drive'): Promise<RouteResponse> {
    const response = await axios.post(`${API_BASE_URL}/plan-route/place`, {
      place_name: placeName,
      network_type: networkType,
    });
    return response.data;
  }

  async getRoute(routeId: string): Promise<RouteResponse> {
    const response = await axios.get(`${API_BASE_URL}/route/${routeId}`);
    return response.data;
  }

  async listRoutes(): Promise<{ routes: any[] }> {
    const response = await axios.get(`${API_BASE_URL}/routes`);
    return response.data;
  }

  async exportRoute(routeId: string, format: string): Promise<void> {
    const response = await axios.get(`${API_BASE_URL}/export/${routeId}/${format}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `route_${routeId}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  connectWebSocket(onMessage: (progress: RouteProgress) => void): WebSocket {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status) {
          onMessage(data as RouteProgress);
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }
}

export default new RouteAPI();