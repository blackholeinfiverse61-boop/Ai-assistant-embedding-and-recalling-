#!/usr/bin/env python3
"""
Debug script to test the search functionality in detail.
"""

import sys
import os

# Add the chandresh directory to the path so we can import the service
sys.path.append(os.path.join(os.path.dirname(__file__)))

from embedding_service import embedding_service

def debug_search():
    """Debug the search functionality."""
    print("Debugging search functionality...")
    
    # Test search with text that should match our test data
    search_text = "hotel booking"
    print(f"\nSearching for: '{search_text}'")
    results = embedding_service.search_similar_items(query_text=search_text, top_k=5)
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['item_type']} {result['item_id']}: score={result['score']:.6f}")
        print(f"     Text: '{result['text']}'")
    
    # Test with another query
    search_text = "flight information"
    print(f"\nSearching for: '{search_text}'")
    results = embedding_service.search_similar_items(query_text=search_text, top_k=5)
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['item_type']} {result['item_id']}: score={result['score']:.6f}")
        print(f"     Text: '{result['text']}'")

if __name__ == "__main__":
    debug_search()