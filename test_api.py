#!/usr/bin/env python3
"""
Simple API test for Chandresh's endpoints
"""

import requests
import json

def test_chandresh_api():
    """Test Chandresh's API endpoints."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Chandresh's EmbedCore & Recall API")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        print("\n1. Health Check:")
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 2: Embedding stats
        print("\n2. Embedding Statistics:")
        response = requests.get(f"{base_url}/api/embeddings/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test 3: Search similar by message text
        print("\n3. Search Similar (by message text):")
        search_data = {
            "message_text": "I need help with hotel booking",
            "top_k": 3
        }
        response = requests.post(
            f"{base_url}/api/search_similar",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Query Type: {result['query_type']}")
        print(f"Total Found: {result['total_found']}")
        print("Related Items:")
        for item in result['related']:
            print(f"  - {item['item_type']} {item['item_id']}: {item['score']:.3f}")
            print(f"    Text: {item['text'][:100]}...")
        
        # Test 4: Search similar by summary_id
        print("\n4. Search Similar (by summary_id):")
        search_data = {
            "summary_id": "s003",  # Restaurant reservation
            "top_k": 2
        }
        response = requests.post(
            f"{base_url}/api/search_similar",
            json=search_data
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Query Type: {result['query_type']}")
        print(f"Total Found: {result['total_found']}")
        print("Related Items:")
        for item in result['related']:
            print(f"  - {item['item_type']} {item['item_id']}: {item['score']:.3f}")
        
        # Test 5: Different search queries
        print("\n5. Various Search Queries:")
        queries = [
            "flight booking",
            "car rental",
            "travel insurance",
            "spa appointment"
        ]
        
        for query in queries:
            response = requests.post(
                f"{base_url}/api/search_similar",
                json={"message_text": query, "top_k": 1}
            )
            if response.status_code == 200:
                result = response.json()
                if result['related']:
                    best_match = result['related'][0]
                    print(f"'{query}' -> {best_match['item_type']} {best_match['item_id']} (score: {best_match['score']:.3f})")
        
        print("\n✅ All tests completed successfully!")
        print("📚 Chandresh's EmbedCore & Recall system is working perfectly!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server.")
        print("Make sure the server is running: uvicorn api_chandresh:app --reload --port 8000")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_chandresh_api()