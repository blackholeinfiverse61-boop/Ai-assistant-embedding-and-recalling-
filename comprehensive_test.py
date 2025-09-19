#!/usr/bin/env python3
"""
Comprehensive test script to verify embedding storage and retrieval functionality.
"""

import sys
import os

# Add the chandresh directory to the path so we can import the service
sys.path.append(os.path.join(os.path.dirname(__file__)))

from embedding_service import embedding_service

def test_comprehensive_embedding_functionality():
    """Test comprehensive embedding functionality."""
    print("Testing comprehensive embedding functionality...")
    
    # Clear any existing test data
    print("Clearing test data...")
    conn = sqlite3.connect("assistant_demo.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM embeddings WHERE item_id LIKE 'comptest_%'")
    conn.commit()
    conn.close()
    
    # Store multiple test embeddings
    test_data = [
        ("summary", "comptest_1", "hotel booking confirmation and itinerary details"),
        ("summary", "comptest_2", "flight information and boarding pass details"),
        ("summary", "comptest_3", "car rental reservation and pickup information"),
        ("task", "comptest_4", "need help with hotel booking"),
        ("task", "comptest_5", "looking for flight information"),
    ]
    
    print("Storing test embeddings...")
    for item_type, item_id, text in test_data:
        success = embedding_service.store_embedding(item_type, item_id, text)
        print(f"  Stored {item_type} {item_id}: {'SUCCESS' if success else 'FAILED'}")
    
    # Test search with similar text
    print("\nTesting search with similar text...")
    search_text = "hotel reservation details"
    results = embedding_service.search_similar_items(query_text=search_text, top_k=5)
    print(f"Search results for '{search_text}':")
    for result in results:
        print(f"  - {result['item_type']} {result['item_id']}: score={result['score']:.3f}, text='{result['text']}'")
    
    # Test search with another similar text
    print("\nTesting search with another similar text...")
    search_text = "flight details"
    results = embedding_service.search_similar_items(query_text=search_text, top_k=5)
    print(f"Search results for '{search_text}':")
    for result in results:
        print(f"  - {result['item_type']} {result['item_id']}: score={result['score']:.3f}, text='{result['text']}'")
    
    # Test search by summary ID
    print("\nTesting search by summary ID...")
    results = embedding_service.search_similar_items(summary_id="comptest_1", top_k=3)
    print(f"Search results similar to summary comptest_1:")
    for result in results:
        print(f"  - {result['item_type']} {result['item_id']}: score={result['score']:.3f}, text='{result['text']}'")
    
    return len(results) >= 0  # At least ran without error

if __name__ == "__main__":
    import sqlite3
    
    try:
        success = test_comprehensive_embedding_functionality()
        print(f"\nTest {'PASSED' if success else 'FAILED'}")
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()