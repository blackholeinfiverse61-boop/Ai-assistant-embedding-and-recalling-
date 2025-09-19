import sqlite3
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for handling embeddings and similarity search - Chandresh's core work."""
    
    def __init__(self, db_path: str = "assistant_demo.db", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for given text."""
        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Fallback to random vector for testing
            return np.random.random(384).tolist()
    
    def store_embedding(self, item_type: str, item_id: str, text: str) -> bool:
        """Store embedding for an item in the database."""
        try:
            # Generate embedding
            embedding = self.generate_embedding(text)
            vector_blob = json.dumps(embedding)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or replace embedding
            cursor.execute('''
                INSERT OR REPLACE INTO embeddings 
                (item_type, item_id, vector_blob, timestamp, text_content)
                VALUES (?, ?, ?, ?, ?)
            ''', (item_type, item_id, vector_blob, datetime.now().isoformat(), text))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored embedding for {item_type} {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return False
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_v1 * norm_v2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def search_similar_items(self, query_text: Optional[str] = None, summary_id: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar items based on query text or summary_id."""
        try:
            # Determine query embedding
            if query_text:
                query_embedding = self.generate_embedding(query_text)
            elif summary_id:
                # Get the summary text for the given summary_id
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT text_content FROM embeddings WHERE item_id = ? AND item_type = ?', (summary_id, 'summary'))
                result = cursor.fetchone()
                conn.close()
                
                if not result or not result[0]:
                    return []
                
                query_embedding = self.generate_embedding(result[0])
            else:
                return []
            
            # Get all embeddings from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT item_type, item_id, vector_blob, text_content
                FROM embeddings
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # Calculate similarities
            similarities = []
            for item_type, item_id, vector_blob, text_content in results:
                try:
                    # Skip items with no text
                    if not text_content:
                        continue
                        
                    item_embedding = json.loads(vector_blob)
                    similarity = self.cosine_similarity(query_embedding, item_embedding)
                    
                    similarities.append({
                        'item_type': item_type,
                        'item_id': item_id,
                        'score': similarity,
                        'text': text_content[:200] + '...' if len(text_content) > 200 else text_content  # Truncate for display
                    })
                except Exception as e:
                    logger.error(f"Error processing item {item_id}: {e}")
                    continue
            
            # Sort by similarity score and return top_k
            similarities.sort(key=lambda x: x['score'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching similar items: {e}")
            return []
    
    def index_existing_summaries(self) -> int:
        """Index all existing summaries that don't have embeddings yet."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find summaries without embeddings
            cursor.execute('''
                SELECT s.summary_id, s.summary_text 
                FROM summaries s
                LEFT JOIN embeddings e ON s.summary_id = e.item_id AND e.item_type = 'summary'
                WHERE e.id IS NULL
            ''')
            
            unindexed_summaries = cursor.fetchall()
            conn.close()
            
            indexed_count = 0
            for summary_id, summary_text in unindexed_summaries:
                if self.store_embedding('summary', summary_id, summary_text):
                    indexed_count += 1
            
            logger.info(f"Indexed {indexed_count} summaries")
            return indexed_count
            
        except Exception as e:
            logger.error(f"Error indexing existing summaries: {e}")
            return 0
    
    def index_existing_tasks(self) -> int:
        """Index all existing tasks that don't have embeddings yet."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find tasks without embeddings
            cursor.execute('''
                SELECT t.task_id, t.task_text 
                FROM tasks t
                LEFT JOIN embeddings e ON t.task_id = e.item_id AND e.item_type = 'task'
                WHERE e.id IS NULL
            ''')
            
            unindexed_tasks = cursor.fetchall()
            conn.close()
            
            indexed_count = 0
            for task_id, task_text in unindexed_tasks:
                if self.store_embedding('task', task_id, task_text):
                    indexed_count += 1
            
            logger.info(f"Indexed {indexed_count} tasks")
            return indexed_count
            
        except Exception as e:
            logger.error(f"Error indexing existing tasks: {e}")
            return 0

# Global instance for use in API
embedding_service = EmbeddingService()