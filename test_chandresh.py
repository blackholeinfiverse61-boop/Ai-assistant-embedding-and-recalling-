import pytest
import sqlite3
import json
import tempfile
import os
from datetime import datetime
from embedding_service import EmbeddingService

class TestEmbeddingService:
    """Unit tests for Chandresh's EmbeddingService."""
    
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
        
        # Insert test data
        cursor.execute('''
            INSERT INTO summaries (summary_id, user_id, summary_text, timestamp)
            VALUES ('s1', 'user1', 'User wants to book a hotel room', ?),
                   ('s2', 'user1', 'User needs flight information', ?),
                   ('s3', 'user2', 'User asking about restaurant reservations', ?)
        ''', (datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
        
        cursor.execute('''
            INSERT INTO tasks (task_id, summary_id, user_id, task_text, timestamp)
            VALUES ('t1', 's1', 'user1', 'Find available hotel rooms in downtown area', ?),
                   ('t2', 's2', 'user1', 'Check flight schedules to New York', ?),
                   ('t3', 's3', 'user2', 'Search for Italian restaurants with availability', ?)
        ''', (datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        yield path
        
        # Cleanup
        os.unlink(path)
    
    @pytest.fixture
    def embedding_service(self, temp_db):
        """Create EmbeddingService instance with test database."""
        return EmbeddingService(db_path=temp_db, model_name="all-MiniLM-L6-v2")
    
    def test_generate_embedding(self, embedding_service):
        """Test embedding generation."""
        text = "This is a test sentence"
        embedding = embedding_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    def test_store_embedding(self, embedding_service, temp_db):
        """Test storing embeddings in database."""
        # Store an embedding
        success = embedding_service.store_embedding(
            item_type="summary",
            item_id="s1",
            text="User wants to book a hotel room"
        )
        
        assert success is True
        
        # Verify it was stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM embeddings WHERE item_id = ?', ('s1',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[1] == "summary"  # item_type
        assert result[2] == "s1"       # item_id
        
        # Verify vector_blob is valid JSON
        vector_data = json.loads(result[3])
        assert isinstance(vector_data, list)
        assert len(vector_data) > 0
    
    def test_cosine_similarity(self, embedding_service):
        """Test cosine similarity calculation."""
        vec1 = [1, 0, 0]
        vec2 = [1, 0, 0]
        vec3 = [0, 1, 0]
        
        # Identical vectors should have similarity of 1
        sim1 = embedding_service.cosine_similarity(vec1, vec2)
        assert abs(sim1 - 1.0) < 0.001
        
        # Orthogonal vectors should have similarity of 0
        sim2 = embedding_service.cosine_similarity(vec1, vec3)
        assert abs(sim2 - 0.0) < 0.001
    
    def test_search_similar_items_by_text(self, embedding_service, temp_db):
        """Test searching similar items by query text."""
        # First, store some embeddings
        embedding_service.store_embedding("summary", "s1", "User wants to book a hotel room")
        embedding_service.store_embedding("summary", "s2", "User needs flight information")
        embedding_service.store_embedding("task", "t1", "Find available hotel rooms in downtown area")
        
        # Search for similar items
        results = embedding_service.search_similar_items(
            query_text="looking for hotel accommodation",
            top_k=2
        )
        
        assert isinstance(results, list)
        assert len(results) <= 2
        
        if results:
            # Check result structure
            result = results[0]
            assert 'item_type' in result
            assert 'item_id' in result
            assert 'score' in result
            assert 'text' in result
            assert isinstance(result['score'], float)
            assert 0 <= result['score'] <= 1
    
    def test_search_similar_items_by_summary_id(self, embedding_service, temp_db):
        """Test searching similar items by summary_id."""
        # Store embeddings
        embedding_service.store_embedding("summary", "s1", "User wants to book a hotel room")
        embedding_service.store_embedding("summary", "s2", "User needs flight information")
        
        # Search using summary_id
        results = embedding_service.search_similar_items(summary_id="s1", top_k=3)
        
        assert isinstance(results, list)
        # Should find at least the summary itself
    
    def test_index_existing_summaries(self, embedding_service, temp_db):
        """Test indexing existing summaries."""
        # Initially no embeddings
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        initial_count = cursor.fetchone()[0]
        conn.close()
        
        # Index existing summaries
        indexed_count = embedding_service.index_existing_summaries()
        
        # Should have indexed the 3 test summaries
        assert indexed_count == 3
        
        # Verify embeddings were created
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM embeddings WHERE item_type = "summary"')
        final_count = cursor.fetchone()[0]
        conn.close()
        
        assert final_count == 3
    
    def test_index_existing_tasks(self, embedding_service, temp_db):
        """Test indexing existing tasks."""
        # Index existing tasks
        indexed_count = embedding_service.index_existing_tasks()
        
        # Should have indexed the 3 test tasks
        assert indexed_count == 3
        
        # Verify embeddings were created
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM embeddings WHERE item_type = "task"')
        final_count = cursor.fetchone()[0]
        conn.close()
        
        assert final_count == 3
    
    def test_empty_search_results(self, embedding_service):
        """Test search with no matching results."""
        results = embedding_service.search_similar_items(query_text="completely unrelated query")
        assert isinstance(results, list)
        # Should return empty list or low-similarity results

class TestIntegration:
    """Integration tests for Chandresh's API endpoints."""
    
    def test_api_search_similar_endpoint(self):
        """Test the search_similar API endpoint."""
        from fastapi.testclient import TestClient
        from api_chandresh import app
        
        client = TestClient(app)
        
        # Test with message_text
        response = client.post("/api/search_similar", json={
            "message_text": "I need help with booking",
            "top_k": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "related" in data
        assert "query_type" in data
        assert "total_found" in data
        assert data["query_type"] == "message_text"
        assert isinstance(data["related"], list)
    
    def test_api_embedding_stats(self):
        """Test the embedding stats endpoint."""
        from fastapi.testclient import TestClient
        from api_chandresh import app
        
        client = TestClient(app)
        
        response = client.get("/api/embeddings/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_embeddings" in data
        assert "by_type" in data
        assert "service_status" in data
    
    def test_api_health_check(self):
        """Test the health check endpoint."""
        from fastapi.testclient import TestClient
        from api_chandresh import app
        
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["owner"] == "chandresh"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])