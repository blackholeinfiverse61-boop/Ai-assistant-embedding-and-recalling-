#!/usr/bin/env python3
"""
Demo Data Generator - Chandresh's test data utility

This script generates sample data for testing the embedding and search functionality.
"""

import sqlite3
import json
from datetime import datetime, timedelta
import random

def generate_demo_data(db_path: str = "assistant_demo.db"):
    """Generate demo data for testing Chandresh's work."""
    
    # Sample data
    sample_summaries = [
        ("s001", "user1", "User wants to book a hotel room in downtown for weekend", "Business travel booking request"),
        ("s002", "user1", "User needs flight information from NYC to LA", "Flight information inquiry"), 
        ("s003", "user2", "User asking about restaurant reservations for anniversary dinner", "Restaurant reservation request"),
        ("s004", "user3", "User wants to cancel existing hotel booking", "Hotel cancellation request"),
        ("s005", "user2", "User needs help with travel insurance options", "Travel insurance inquiry"),
        ("s006", "user4", "User looking for car rental near airport", "Car rental request"),
        ("s007", "user1", "User wants to upgrade flight seat to business class", "Flight upgrade request"),
        ("s008", "user3", "User asking about pet-friendly hotel options", "Pet-friendly accommodation inquiry"),
        ("s009", "user5", "User needs train schedule information", "Train schedule inquiry"),
        ("s010", "user2", "User wants to book spa appointment at hotel", "Hotel spa booking request")
    ]
    
    sample_tasks = [
        ("t001", "s001", "user1", "Find available hotel rooms in downtown area for weekend dates"),
        ("t002", "s002", "user1", "Check flight schedules and prices from NYC to LA"),
        ("t003", "s003", "user2", "Search for Italian restaurants with availability for anniversary"),
        ("t004", "s004", "user3", "Process hotel booking cancellation and refund"),
        ("t005", "s005", "user2", "Research travel insurance providers and coverage options"),
        ("t006", "s006", "user4", "Find car rental companies near airport with good rates"),
        ("t007", "s007", "user1", "Check availability and cost for flight seat upgrade"),
        ("t008", "s008", "user3", "Locate pet-friendly hotels with appropriate amenities"),
        ("t009", "s009", "user5", "Provide train schedule and booking information"),
        ("t010", "s010", "user2", "Book spa services at user's hotel location")
    ]
    
    sample_responses = [
        ("r001", "t001", "user1", "I found 5 available hotels in downtown. The Grand Plaza has rooms starting at $200/night.", "helpful", "ok"),
        ("r002", "t002", "user1", "Here are 3 direct flights from NYC to LA: American Airlines at 9am ($450), Delta at 2pm ($480), United at 6pm ($420).", "informative", "ok"),
        ("r003", "t003", "user2", "I found La Bella Vista restaurant with availability for your anniversary. They have a romantic table for two at 7pm.", "warm", "ok"),
        ("r004", "t004", "user3", "Your hotel booking has been successfully cancelled. The full refund of $350 will be processed within 3-5 business days.", "professional", "ok"),
        ("r005", "t005", "user2", "I recommend checking World Nomads or Allianz for comprehensive travel insurance. Both offer good coverage for international trips.", "helpful", "ok")
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert sample summaries
        for summary_id, user_id, message_text, summary_text in sample_summaries:
            cursor.execute('''
                INSERT OR REPLACE INTO summaries (summary_id, user_id, message_text, summary_text, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (summary_id, user_id, message_text, summary_text, datetime.now().isoformat()))
        
        # Insert sample tasks  
        for task_id, summary_id, user_id, task_text in sample_tasks:
            cursor.execute('''
                INSERT OR REPLACE INTO tasks (task_id, summary_id, user_id, task_text, priority, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_id, summary_id, user_id, task_text, "medium", datetime.now().isoformat()))
        
        # Insert sample responses
        for response_id, task_id, user_id, response_text, tone, status in sample_responses:
            cursor.execute('''
                INSERT OR REPLACE INTO responses (response_id, task_id, user_id, response_text, tone, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (response_id, task_id, user_id, response_text, tone, status, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"Generated demo data:")
        print(f"  - {len(sample_summaries)} summaries")
        print(f"  - {len(sample_tasks)} tasks") 
        print(f"  - {len(sample_responses)} responses")
        print(f"Data saved to {db_path}")
        
    except Exception as e:
        print(f"Error generating demo data: {e}")

if __name__ == "__main__":
    # Initialize database first
    from database import init_database
    init_database()
    
    # Generate demo data
    generate_demo_data()
    
    print("\nTo test Chandresh's work:")
    print("1. Run: python rebuild_embeddings.py")
    print("2. Run: uvicorn api_chandresh:app --reload --port 8000")
    print("3. Test: curl -X POST 'http://localhost:8000/api/search_similar' -H 'Content-Type: application/json' -d '{\"message_text\":\"hotel booking\"}'")