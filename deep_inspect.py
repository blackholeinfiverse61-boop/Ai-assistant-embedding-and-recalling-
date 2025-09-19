#!/usr/bin/env python3
"""
Deep inspection of the database to understand why search isn't working.
"""

import sqlite3
import json

def deep_inspect():
    """Deep inspect the database contents."""
    print("Deep inspecting database...")
    
    conn = sqlite3.connect("assistant_demo.db")
    cursor = conn.cursor()
    
    # Show all embeddings with their vector blobs
    cursor.execute("SELECT item_type, item_id, vector_blob FROM embeddings WHERE item_id LIKE 'comptest_%'")
    embeddings = cursor.fetchall()
    print(f"\nFound {len(embeddings)} test embeddings:")
    for item_type, item_id, vector_blob in embeddings:
        print(f"  {item_type} {item_id}: vector length = {len(vector_blob)} chars")
        # Try to parse the vector
        try:
            vector = json.loads(vector_blob)
            print(f"    Vector parsed successfully, length = {len(vector)}")
        except Exception as e:
            print(f"    Error parsing vector: {e}")
    
    # Check if we have summaries and tasks tables with data
    try:
        cursor.execute("SELECT COUNT(*) FROM summaries")
        summaries_count = cursor.fetchone()[0]
        print(f"\nSummaries table has {summaries_count} records")
    except Exception as e:
        print(f"\nError accessing summaries table: {e}")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM tasks")
        tasks_count = cursor.fetchone()[0]
        print(f"Tasks table has {tasks_count} records")
    except Exception as e:
        print(f"Error accessing tasks table: {e}")
    
    # Show the actual query being used in search
    print("\nQuery used in search_similar_items:")
    query = '''
        SELECT e.item_type, e.item_id, e.vector_blob, 
               CASE 
                   WHEN e.item_type = 'summary' THEN s.summary_text
                   WHEN e.item_type = 'task' THEN t.task_text
                   ELSE 'No text available'
               END as text
        FROM embeddings e
        LEFT JOIN summaries s ON e.item_type = 'summary' AND e.item_id = s.summary_id
        LEFT JOIN tasks t ON e.item_type = 'task' AND e.item_id = t.task_id
        WHERE e.item_id LIKE 'comptest_%'
    '''
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"Query returned {len(results)} rows:")
    for item_type, item_id, vector_blob, text in results:
        print(f"  {item_type} {item_id}: text = '{text}'")
    
    conn.close()

if __name__ == "__main__":
    deep_inspect()