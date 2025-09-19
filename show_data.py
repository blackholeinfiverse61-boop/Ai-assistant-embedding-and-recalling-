#!/usr/bin/env python3
"""
Database Data Inspection - Show all data in assistant_demo.db
"""

import sqlite3
import json

def show_database_data(db_path: str = "assistant_demo.db"):
    """Display all data in the database in a readable format."""
    
    print("📊 DATABASE CONTENT OVERVIEW")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        tables = [table[0] for table in cursor.fetchall()]
        
        for table_name in tables:
            print(f"\n🔧 TABLE: {table_name.upper()}")
            print("-" * 40)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"📈 Total rows: {count}")
            
            if count > 0:
                # Get all data
                cursor.execute(f"SELECT * FROM {table_name};")
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"📋 Columns: {', '.join(columns)}")
                print("\n📄 Data:")
                
                for i, row in enumerate(rows, 1):
                    print(f"\n  Row {i}:")
                    for col, val in zip(columns, row):
                        if col == 'vector_blob' and val:
                            # Show truncated vector for readability
                            vector_preview = str(val)[:100] + "..." if len(str(val)) > 100 else str(val)
                            print(f"    {col}: {vector_preview}")
                        else:
                            print(f"    {col}: {val}")
            else:
                print("   (No data)")
        
        conn.close()
        
        # Summary
        print(f"\n🎯 SUMMARY")
        print("=" * 60)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM summaries;")
        summaries_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks;")
        tasks_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM responses;")
        responses_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM embeddings;")
        embeddings_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM coach_feedback;")
        feedback_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM metrics;")
        metrics_count = cursor.fetchone()[0]
        
        print(f"📊 Data Distribution:")
        print(f"   📝 Summaries: {summaries_count} records")
        print(f"   📋 Tasks: {tasks_count} records")
        print(f"   💬 Responses: {responses_count} records")
        print(f"   🧠 Embeddings: {embeddings_count} records")
        print(f"   📈 Coach Feedback: {feedback_count} records")
        print(f"   📊 Metrics: {metrics_count} records")
        print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   🎯 Total Records: {summaries_count + tasks_count + responses_count + embeddings_count + feedback_count + metrics_count}")
        
        # Show data flow
        if summaries_count > 0 or tasks_count > 0 or responses_count > 0:
            print(f"\n🔄 DATA PIPELINE STATUS:")
            print(f"   Message → Summary ({summaries_count} ✅)")
            print(f"   Summary → Task ({tasks_count} ✅)")
            print(f"   Task → Response ({responses_count} ✅)")
            print(f"   Items → Embeddings ({embeddings_count} ✅)")
            print(f"   Response → Feedback ({feedback_count} {'✅' if feedback_count > 0 else '⏳ Ready'})")
            print(f"   API → Metrics ({metrics_count} {'✅' if metrics_count > 0 else '⏳ Ready'})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    show_database_data()