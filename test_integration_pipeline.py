#!/usr/bin/env python3
"""
Integration tests for the full pipeline flow
"""

import pytest
import sqlite3
import json
import tempfile
import os
from datetime import datetime
from fastapi.testclient import TestClient

# Test the full pipeline flow
class TestPipelineIntegration:
    """Integration tests for the full pipeline flow."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client for pipeline API."""
        from api_pipeline import app
        return TestClient(app)
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Initialize test database
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create required tables
        cursor.execute('''
            CREATE TABLE embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_id TEXT NOT NULL,
                vector_blob TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                UNIQUE(item_type, item_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE summaries (
                summary_id TEXT PRIMARY KEY,
                user_id TEXT,
                message_text TEXT,
                summary_text TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE tasks (
                task_id TEXT PRIMARY KEY,
                summary_id TEXT,
                user_id TEXT,
                task_text TEXT,
                priority TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE responses (
                response_id TEXT PRIMARY KEY,
                task_id TEXT,
                user_id TEXT,
                response_text TEXT,
                tone TEXT,
                status TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE coach_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_id TEXT,
                task_id TEXT,
                response_id TEXT,
                score INTEGER,
                comment TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield path
        
        # Cleanup
        os.unlink(path)
    
    def test_full_pipeline_flow(self, test_client, temp_db, monkeypatch):
        """Test the full pipeline flow from message to feedback."""
        # Mock the database path
        monkeypatch.setattr("api_pipeline.sqlite3.connect", lambda x: sqlite3.connect(temp_db))
        monkeypatch.setattr("embedding_service.sqlite3.connect", lambda x: sqlite3.connect(temp_db))
        
        # Step 1: Summarize a message
        summarize_request = {
            "message_text": "I need help booking a hotel room for my upcoming trip to New York.",
            "user_id": "test_user_123"
        }
        
        response = test_client.post("/api/summarize", json=summarize_request)
        assert response.status_code == 200
        
        summarize_result = response.json()
        assert "summary_id" in summarize_result
        assert "summary_text" in summarize_result
        assert "confidence_score" in summarize_result
        assert summarize_result["confidence_score"] >= 0.0
        assert summarize_result["confidence_score"] <= 1.0
        
        summary_id = summarize_result["summary_id"]
        
        # Step 2: Process the summary to generate a task
        process_request = {
            "summary_id": summary_id,
            "user_id": "test_user_123"
        }
        
        response = test_client.post("/api/process_summary", json=process_request)
        assert response.status_code == 200
        
        process_result = response.json()
        assert "task_id" in process_result
        assert "task_text" in process_result
        assert "priority" in process_result
        assert "confidence_score" in process_result
        assert process_result["confidence_score"] >= 0.0
        assert process_result["confidence_score"] <= 1.0
        
        task_id = process_result["task_id"]
        
        # Step 3: Submit positive feedback
        feedback_request = {
            "summary_id": summary_id,
            "task_id": task_id,
            "score": 1,
            "comment": "Great summary and task generation!"
        }
        
        response = test_client.post("/api/feedback", json=feedback_request)
        assert response.status_code == 200
        
        feedback_result = response.json()
        assert feedback_result["status"] == "success"
        
        # Step 4: Verify feedback was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM coach_feedback WHERE summary_id = ? AND task_id = ? AND score = 1', 
                      (summary_id, task_id))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1
    
    def test_pipeline_with_negative_feedback(self, test_client, temp_db, monkeypatch):
        """Test pipeline with negative feedback."""
        # Mock the database path
        monkeypatch.setattr("api_pipeline.sqlite3.connect", lambda x: sqlite3.connect(temp_db))
        monkeypatch.setattr("embedding_service.sqlite3.connect", lambda x: sqlite3.connect(temp_db))
        
        # Step 1: Summarize a message
        summarize_request = {
            "message_text": "I need assistance with my flight cancellation.",
            "user_id": "test_user_456"
        }
        
        response = test_client.post("/api/summarize", json=summarize_request)
        assert response.status_code == 200
        
        summarize_result = response.json()
        summary_id = summarize_result["summary_id"]
        
        # Step 2: Process the summary
        process_request = {
            "summary_id": summary_id,
            "user_id": "test_user_456"
        }
        
        response = test_client.post("/api/process_summary", json=process_request)
        assert response.status_code == 200
        
        process_result = response.json()
        task_id = process_result["task_id"]
        
        # Step 3: Submit negative feedback
        feedback_request = {
            "summary_id": summary_id,
            "task_id": task_id,
            "score": -1,
            "comment": "The task generated was not relevant to my request."
        }
        
        response = test_client.post("/api/feedback", json=feedback_request)
        assert response.status_code == 200
        
        feedback_result = response.json()
        assert feedback_result["status"] == "success"
        
        # Step 4: Verify negative feedback was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM coach_feedback WHERE summary_id = ? AND task_id = ? AND score = -1', 
                      (summary_id, task_id))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1
    
    def test_pipeline_configuration(self, test_client):
        """Test pipeline configuration endpoints."""
        # Get current configuration
        response = test_client.get("/api/pipeline/config")
        assert response.status_code == 200
        
        config = response.json()
        assert "enable_summarization" in config
        assert "enable_task_generation" in config
        assert "enable_embedding_storage" in config
        assert "retry_attempts" in config
        assert "timeout_seconds" in config
        
        # Update configuration
        new_config = {
            "enable_summarization": False,
            "enable_task_generation": True,
            "enable_embedding_storage": False,
            "retry_attempts": 5,
            "timeout_seconds": 60
        }
        
        response = test_client.put("/api/pipeline/config", json=new_config)
        assert response.status_code == 200
        
        updated_config = response.json()
        assert updated_config["enable_summarization"] == False
        assert updated_config["retry_attempts"] == 5
    
    def test_pipeline_metrics(self, test_client, temp_db, monkeypatch):
        """Test pipeline metrics endpoint."""
        # Mock the database path
        monkeypatch.setattr("api_pipeline.sqlite3.connect", lambda x: sqlite3.connect(temp_db))
        
        # Get metrics
        response = test_client.get("/api/metrics/summary")
        assert response.status_code == 200
        
        metrics = response.json()
        assert "summaries_processed" in metrics
        assert "tasks_generated" in metrics
        assert "feedback_received" in metrics
        assert "embeddings_stored" in metrics
        assert "average_feedback_score" in metrics
        assert "feedback_distribution" in metrics

class TestChandreshIntegration:
    """Integration tests for Chandresh's existing endpoints with the new pipeline."""
    
    def test_search_similar_after_pipeline_processing(self, test_client, temp_db, monkeypatch):
        """Test that embeddings are properly stored and searchable after pipeline processing."""
        # Mock the database path
        monkeypatch.setattr("api_pipeline.sqlite3.connect", lambda x: sqlite3.connect(temp_db))
        monkeypatch.setattr("embedding_service.sqlite3.connect", lambda x: sqlite3.connect(temp_db))
        
        # Step 1: Summarize a message (this should store an embedding)
        summarize_request = {
            "message_text": "I need help with hotel booking in downtown area.",
            "user_id": "test_user_789"
        }
        
        response = test_client.post("/api/summarize", json=summarize_request)
        assert response.status_code == 200
        
        summarize_result = response.json()
        summary_id = summarize_result["summary_id"]
        
        # Step 2: Process the summary (this should store another embedding)
        process_request = {
            "summary_id": summary_id,
            "user_id": "test_user_789"
        }
        
        response = test_client.post("/api/process_summary", json=process_request)
        assert response.status_code == 200
        
        process_result = response.json()
        task_id = process_result["task_id"]
        
        # Step 3: Search for similar items using Chandresh's endpoint
        # Import the original API client
        from api_chandresh import app as chandresh_app
        chandresh_client = TestClient(chandresh_app)
        
        # Search by message text
        search_request = {
            "message_text": "I'm looking for hotel accommodations",
            "top_k": 3
        }
        
        response = chandresh_client.post("/api/search_similar", json=search_request)
        assert response.status_code == 200
        
        search_result = response.json()
        assert "related" in search_result
        assert "query_type" in search_result
        assert "total_found" in search_result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])