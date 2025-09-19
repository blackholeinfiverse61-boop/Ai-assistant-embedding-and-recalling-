#!/usr/bin/env python3
"""
Complete Setup and Test Script for Chandresh's Work

This script demonstrates the full working solution by:
1. Setting up the database
2. Generating demo data
3. Building embeddings
4. Testing the API endpoints
"""

import subprocess
import sys
import time
import requests
import json
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}...")
        else:
            print(f"❌ {description} - Failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False
    
    return True

def test_api_endpoints():
    """Test the API endpoints once server is running."""
    base_url = "http://localhost:8000"
    
    print(f"\n🧪 Testing API endpoints...")
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test health check
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test embedding stats
        response = requests.get(f"{base_url}/api/embeddings/stats")
        if response.status_code == 200:
            print("✅ Embedding stats endpoint working")
            print(f"Stats: {response.json()}")
        else:
            print(f"❌ Embedding stats failed: {response.status_code}")
        
        # Test search similar with message text
        search_request = {
            "message_text": "I need help booking a hotel room",
            "top_k": 3
        }
        
        response = requests.post(
            f"{base_url}/api/search_similar",
            json=search_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Search similar by message text working")
            result = response.json()
            print(f"Found {result['total_found']} related items:")
            for item in result['related']:
                print(f"  - {item['item_type']} {item['item_id']}: {item['score']:.3f}")
        else:
            print(f"❌ Search similar failed: {response.status_code}")
            print(f"Error: {response.text}")
        
        # Test search similar with summary_id
        search_request = {
            "summary_id": "s001",
            "top_k": 3
        }
        
        response = requests.post(
            f"{base_url}/api/search_similar",
            json=search_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Search similar by summary_id working")
            result = response.json()
            print(f"Found {result['total_found']} related items for summary s001")
        else:
            print(f"❌ Search similar by summary_id failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure it's running.")
        return False
    except Exception as e:
        print(f"❌ API testing failed: {e}")
        return False

def start_api_server():
    """Start the API server in a subprocess."""
    print("\n🌐 Starting API server...")
    server_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "api_chandresh:app", "--reload", "--port", "8000"])
    print("Server started with PID:", server_process.pid)
    return server_process

def main():
    """Main setup and test function."""
    print("🚀 Setting up and testing Chandresh's EmbedCore & Recall implementation")
    print("=" * 70)
    
    # Step 1: Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("⚠️  Dependencies installation failed, continuing anyway...")
    
    # Step 2: Initialize database
    if not run_command("python database.py", "Initializing database"):
        print("❌ Database initialization failed. Exiting.")
        return False
    
    # Step 3: Generate demo data
    if not run_command("python demo_data.py", "Generating demo data"):
        print("❌ Demo data generation failed. Exiting.")
        return False
    
    # Step 4: Build embeddings
    if not run_command("python rebuild_embeddings.py", "Building embeddings"):
        print("❌ Embedding build failed. Exiting.")
        return False
    
    # Step 5: Run tests
    if not run_command("python -m pytest test_chandresh.py -v", "Running unit tests"):
        print("⚠️  Some tests failed, but continuing...")
    
    print(f"\n🎯 Setup complete! Now you can:")
    print(f"1. Start the API server: uvicorn api_chandresh:app --reload --port 8000")
    print(f"2. Test endpoints manually or run test_api_endpoints()")
    print(f"3. View the README_chandresh.md for detailed documentation")
    
    # Ask if user wants to start server for testing
    try:
        start_server_input = input("\n❓ Start API server for testing? (y/n): ").lower().strip()
        if start_server_input == 'y':
            # Start server in background and test
            server_process = start_api_server()
            
            # Give the server time to start
            time.sleep(3)
            
            # Test the endpoints
            test_api_endpoints()
            
            print(f"\n✅ All tests completed!")
            print(f"Server is running at: http://localhost:8000")
            print(f"API docs available at: http://localhost:8000/docs")
            print(f"Press Ctrl+C to stop the server")
            
            # Keep main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n👋 Stopping server...")
                server_process.terminate()
                server_process.wait()
                print(f"👋 Server stopped.")
    
    except KeyboardInterrupt:
        print(f"\n👋 Setup completed successfully!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)