from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime
import time
import asyncio

from embedding_service import embedding_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Assistant API - Chandresh's Endpoints", version="1.0.0")

# Configuration
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

class SearchSimilarRequest(BaseModel):
    """Request model for search_similar endpoint."""
    summary_id: Optional[str] = None
    message_text: Optional[str] = None
    top_k: Optional[int] = 3

class SearchSimilarResponse(BaseModel):
    """Response model for search_similar endpoint."""
    related: List[Dict[str, Any]]
    query_type: str
    total_found: int

class MessageRequest(BaseModel):
    """Request model for message-based search."""
    message_text: str
    user_id: Optional[str] = None

@app.post("/api/search_similar", response_model=SearchSimilarResponse)
async def search_similar(request: SearchSimilarRequest):
    """
    Chandresh's main endpoint: Search for similar summaries/tasks.
    
    Input: { "summary_id": "s123" } or { "message_text": "some text" }
    Output: { "related": [{ "item_type": "summary", "item_id": "s456", "score": 0.87, "text": "..." }] }
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.summary_id and not request.message_text:
            raise HTTPException(
                status_code=400, 
                detail="Either summary_id or message_text must be provided"
            )
        
        # Handle None values by providing default values
        top_k = request.top_k if request.top_k is not None else 3
        message_text = request.message_text if request.message_text is not None else ""
        
        # Retry mechanism
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                # Search for similar items
                if request.summary_id:
                    related_items = embedding_service.search_similar_items(
                        summary_id=request.summary_id, 
                        top_k=top_k
                    )
                    query_type = "summary_id"
                else:
                    related_items = embedding_service.search_similar_items(
                        query_text=message_text, 
                        top_k=top_k
                    )
                    query_type = "message_text"
                
                logger.info(f"Found {len(related_items)} similar items for {query_type} (attempt {attempt + 1})")
                
                # Calculate latency
                latency = time.time() - start_time
                
                # Log metrics
                logger.info(f"Search completed in {latency:.2f} seconds")
                
                return SearchSimilarResponse(
                    related=related_items,
                    query_type=query_type,
                    total_found=len(related_items)
                )
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
        
        # If all retries failed, raise a generic exception if last_exception is None
        if last_exception is not None:
            raise last_exception
        else:
            raise Exception("All retry attempts failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_similar: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/store_embedding")
async def store_embedding(item_type: str, item_id: str, text: str):
    """
    Utility endpoint to manually store embeddings.
    Used for integration with Seeya's summarize endpoint.
    """
    try:
        # Validate input
        if not item_type or not item_id or not text:
            raise HTTPException(status_code=400, detail="item_type, item_id, and text are required")
        
        # Retry mechanism
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                success = embedding_service.store_embedding(item_type, item_id, text)
                
                if success:
                    logger.info(f"Embedding stored for {item_type} {item_id} (attempt {attempt + 1})")
                    return {"status": "success", "message": f"Embedding stored for {item_type} {item_id}"}
                else:
                    raise Exception("Embedding service returned failure")
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed to store embedding: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
        
        # If all retries failed, raise a generic exception if last_exception is None
        if last_exception is not None:
            raise last_exception
        else:
            raise Exception("All retry attempts failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/embeddings/stats")
async def get_embedding_stats():
    """Get statistics about stored embeddings."""
    try:
        import sqlite3
        
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        # Count embeddings by type
        cursor.execute('''
            SELECT item_type, COUNT(*) as count 
            FROM embeddings 
            GROUP BY item_type
        ''')
        
        type_counts = dict(cursor.fetchall())
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_embeddings": total_count,
            "by_type": type_counts,
            "service_status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/reindex")
async def trigger_reindex():
    """Trigger reindexing of all summaries and tasks."""
    try:
        summary_count = embedding_service.index_existing_summaries()
        task_count = embedding_service.index_existing_tasks()
        
        return {
            "status": "success",
            "summaries_indexed": summary_count,
            "tasks_indexed": task_count,
            "total_indexed": summary_count + task_count
        }
        
    except Exception as e:
        logger.error(f"Error during reindexing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "embedding_service", "owner": "chandresh"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)