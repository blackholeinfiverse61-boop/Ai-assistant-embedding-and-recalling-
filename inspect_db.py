#!/usr/bin/env python3
"""
Database inspection script to check the relationship between database.py and assistant_demo.db
"""

import sqlite3
import os

def inspect_database(db_path: str = "assistant_demo.db"):
    """Inspect the database structure and contents."""
    
    print(f"🔍 Inspecting database: {db_path}")
    print("=" * 60)
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} does not exist!")
        return False
    
    file_size = os.path.getsize(db_path)
    print(f"📁 Database file size: {file_size:,} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check each table structure and data
        for table in tables:
            table_name = table[0]
            print(f"\n🔧 Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("  Columns:")
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                constraints = []
                if pk: constraints.append("PRIMARY KEY")
                if not_null: constraints.append("NOT NULL")
                if default: constraints.append(f"DEFAULT {default}")
                
                constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                print(f"    - {name}: {data_type}{constraint_str}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  Data: {count} rows")
            
            # Show sample data if exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                print("  Sample data:")
                for i, row in enumerate(sample_rows):
                    print(f"    Row {i+1}: {row}")
        
        # Check foreign key constraints
        print(f"\n🔗 Foreign Key Constraints:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            fks = cursor.fetchall()
            if fks:
                print(f"  {table_name}:")
                for fk in fks:
                    print(f"    - {fk[3]} → {fk[2]}.{fk[4]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        return False

def verify_schema_consistency():
    """Verify that the database schema matches what database.py creates."""
    
    print(f"\n✅ Schema Consistency Check")
    print("=" * 60)
    
    # Expected tables from database.py
    expected_tables = {
        'embeddings': [
            ('id', 'INTEGER', True, True),  # (name, type, not_null, primary_key)
            ('item_type', 'TEXT', True, False),
            ('item_id', 'TEXT', True, False),
            ('vector_blob', 'TEXT', True, False),
            ('timestamp', 'TEXT', True, False)
        ],
        'summaries': [
            ('summary_id', 'TEXT', False, True),
            ('user_id', 'TEXT', False, False),
            ('message_text', 'TEXT', False, False),
            ('summary_text', 'TEXT', False, False),
            ('timestamp', 'TEXT', False, False)
        ],
        'tasks': [
            ('task_id', 'TEXT', False, True),
            ('summary_id', 'TEXT', False, False),
            ('user_id', 'TEXT', False, False),
            ('task_text', 'TEXT', False, False),
            ('priority', 'TEXT', False, False),
            ('timestamp', 'TEXT', False, False)
        ],
        'responses': [
            ('response_id', 'TEXT', False, True),
            ('task_id', 'TEXT', False, False),
            ('user_id', 'TEXT', False, False),
            ('response_text', 'TEXT', False, False),
            ('tone', 'TEXT', False, False),
            ('status', 'TEXT', False, False),
            ('timestamp', 'TEXT', False, False)
        ],
        'coach_feedback': [
            ('id', 'INTEGER', False, True),
            ('summary_id', 'TEXT', False, False),
            ('task_id', 'TEXT', False, False),
            ('response_id', 'TEXT', False, False),
            ('score', 'INTEGER', False, False),
            ('comment', 'TEXT', False, False),
            ('timestamp', 'TEXT', False, False)
        ],
        'metrics': [
            ('id', 'INTEGER', False, True),
            ('endpoint', 'TEXT', True, False),
            ('status_code', 'INTEGER', False, False),
            ('latency_ms', 'REAL', False, False),
            ('timestamp', 'TEXT', False, False)
        ]
    }
    
    try:
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        # Check each expected table
        for table_name, expected_cols in expected_tables.items():
            print(f"\n🔍 Checking table: {table_name}")
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            if not cursor.fetchone():
                print(f"  ❌ Table {table_name} does not exist!")
                continue
            
            # Get actual schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            actual_cols = cursor.fetchall()
            
            # Convert to comparable format
            actual_schema = {}
            for col in actual_cols:
                col_id, name, data_type, not_null, default, pk = col
                actual_schema[name] = (data_type, bool(not_null), bool(pk))
            
            # Check each expected column
            for exp_name, exp_type, exp_not_null, exp_pk in expected_cols:
                if exp_name in actual_schema:
                    act_type, act_not_null, act_pk = actual_schema[exp_name]
                    
                    issues = []
                    if act_type.upper() != exp_type.upper():
                        issues.append(f"type mismatch: {act_type} vs {exp_type}")
                    if act_pk != exp_pk:
                        issues.append(f"primary key mismatch: {act_pk} vs {exp_pk}")
                    
                    if issues:
                        print(f"  ⚠️  Column {exp_name}: {', '.join(issues)}")
                    else:
                        print(f"  ✅ Column {exp_name}: OK")
                else:
                    print(f"  ❌ Column {exp_name}: MISSING")
            
            # Check for unexpected columns
            for act_name in actual_schema:
                if not any(exp_name == act_name for exp_name, _, _, _ in expected_cols):
                    print(f"  ⚠️  Unexpected column: {act_name}")
        
        conn.close()
        print(f"\n✅ Schema consistency check completed!")
        
    except Exception as e:
        print(f"❌ Error checking schema consistency: {e}")

if __name__ == "__main__":
    # Inspect the database
    success = inspect_database()
    
    if success:
        # Verify schema consistency
        verify_schema_consistency()
    
    print(f"\n🎯 Summary:")
    print(f"database.py creates and manages the SQLite database schema")
    print(f"assistant_demo.db is the actual SQLite database file containing the data")
    print(f"The relationship is: database.py → creates/manages → assistant_demo.db")