#!/usr/bin/env python3
"""
Test the backend API directly without the web UI.
This helps isolate backend issues from frontend issues.
"""

import requests
import time
import sys
import json
import subprocess
import os
import signal

def start_backend_server():
    """Start the backend server in a subprocess."""
    print("Starting backend server...")
    
    # Change to backend directory and start server
    backend_dir = os.path.join(os.path.dirname(__file__), '..', 'web_app', 'backend')
    
    # Start the server process
    env = os.environ.copy()
    process = subprocess.Popen(
        ['python', 'app.py'],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("Waiting for server to be ready...")
    max_wait = 30
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get("http://localhost:8000/")
            if response.status_code == 200:
                print("✓ Server is ready")
                return process
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    
    # If we get here, server didn't start
    process.kill()
    raise Exception("Backend server failed to start within 30 seconds")


def test_api_endpoints(keep_server_running=False):
    """Test the backend API endpoints directly."""
    
    print("="*60)
    print("BACKEND API DIRECT TEST")
    print("="*60)
    
    server_process = None
    
    try:
        # Check if server is already running
        try:
            response = requests.get("http://localhost:8000/", timeout=1)
            print("✓ Using existing backend server")
        except:
            # Start the server
            server_process = start_backend_server()
        
        # Test 1: Root endpoint
        print("\n--- Test 1: Root Endpoint ---")
        try:
            response = requests.get("http://localhost:8000/")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Root endpoint working")
                print(f"  Version: {data.get('version', 'unknown')}")
                print(f"  Endpoints: {len(data.get('endpoints', []))}")
            else:
                print(f"✗ Unexpected status code")
        except Exception as e:
            print(f"✗ Failed: {e}")
        
        # Test 2: Small bounding box
        print("\n--- Test 2: Small Bounding Box ---")
        payload = {
            "north": 37.8705,
            "south": 37.8700,
            "east": -122.2685,
            "west": -122.2690,
            "network_type": "drive"
        }
        
        print(f"Area: ~0.25 km² (1 block)")
        print("Sending request...")
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/api/plan-route/bbox",
                json=payload,
                timeout=60
            )
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Route planning successful")
                if 'route_id' in data:
                    print(f"  Route ID: {data['route_id']}")
                if 'stats' in data:
                    stats = data['stats']
                    print(f"  Edges: {stats.get('total_edges', 'N/A')}")
                    print(f"  Distance: {stats.get('total_distance_km', 'N/A')} km")
            else:
                print(f"✗ Route planning failed")
                print(f"  Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"✗ Request timed out after 60s")
        except Exception as e:
            print(f"✗ Request failed: {e}")
        
        # Test 3: Medium bounding box
        print("\n--- Test 3: Medium Bounding Box ---")
        payload = {
            "north": 37.8720,
            "south": 37.8700,
            "east": -122.2670,
            "west": -122.2700,
            "network_type": "drive"
        }
        
        print(f"Area: ~1 km² (4-6 blocks)")
        print("Sending request...")
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/api/plan-route/bbox",
                json=payload,
                timeout=120
            )
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Route planning successful")
            else:
                print(f"✗ Route planning failed")
                print(f"  Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"✗ Request timed out after 120s")
        except Exception as e:
            print(f"✗ Request failed: {e}")
        
        # Test 4: Place name
        print("\n--- Test 4: Place Name ---")
        payload = {
            "place_name": "Piedmont, California, USA",
            "network_type": "drive"
        }
        
        print(f"Place: {payload['place_name']}")
        print("Sending request...")
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/api/plan-route/place",
                json=payload,
                timeout=180
            )
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Place route planning successful")
            else:
                print(f"✗ Place route planning failed")
                print(f"  Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"✗ Request timed out after 180s")
        except Exception as e:
            print(f"✗ Request failed: {e}")
        
        # Test 5: Invalid request
        print("\n--- Test 5: Invalid Request Handling ---")
        payload = {
            "north": 37.8705,
            "south": 37.8700,
            # Missing east/west
            "network_type": "drive"
        }
        
        print("Sending invalid request (missing coordinates)...")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/plan-route/bbox",
                json=payload,
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code in [400, 422]:
                print(f"✓ Correctly rejected invalid request")
            else:
                print(f"✗ Should have rejected invalid request")
                
        except Exception as e:
            print(f"✗ Request failed: {e}")
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        
    finally:
        # Clean up server process if we started it
        if server_process and not keep_server_running:
            print("\nStopping backend server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✓ Server stopped")


def main():
    """Run the backend API tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test backend API directly')
    parser.add_argument('--keep-server', action='store_true',
                       help='Keep server running after tests')
    args = parser.parse_args()
    
    try:
        test_api_endpoints(keep_server_running=args.keep_server)
        return 0
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())