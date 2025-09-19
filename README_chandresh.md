# Chandresh's Work - EmbedCore & Recall Implementation

This is the complete implementation of Chandresh's responsibilities for the AI Assistant Integration Sprint.

## Overview

Chandresh is responsible for **EmbedCore & Recall** functionality, which enables the AI assistant to find and recall related past conversations, summaries, and tasks using semantic similarity.

## Key Components

### 1. **EmbeddingService** (`embedding_service.py`)
- Core service for generating and storing embeddings
- Uses SentenceTransformer for semantic embeddings
- Handles similarity search with cosine similarity
- Manages database operations for embeddings

### 2. **API Endpoints** (`api_chandresh.py`)
- `POST /api/search_similar` - Main search endpoint
- `POST /api/store_embedding` - Store embeddings manually
- `GET /api/embeddings/stats` - Get embedding statistics
- `POST /api/reindex` - Trigger reindexing
- `GET /health` - Health check

### 3. **Pipeline API Endpoints** (`api_pipeline.py`)
- `POST /api/summarize` - Message summarization
- `POST /api/process_summary` - Task generation from summaries
- `POST /api/feedback` - User feedback collection
- `GET/PUT /api/pipeline/config` - Pipeline configuration
- `GET /api/metrics/summary` - Performance metrics
- `POST /api/rl/process_feedback` - Manual RL agent triggering
- `GET /api/rl/performance` - RL agent performance metrics
- `GET /api/visualizations/*` - Metrics visualizations

### 4. **Reindexing Script** (`rebuild_embeddings.py`)
- Command-line tool for rebuilding embeddings
- Supports selective reindexing by item type
- Includes verification functionality
- Handles model changes and data recovery

### 5. **Database Schema** (`database.py`)
- SQLite database initialization
- Embeddings table with vector storage
- Integration tables for summaries, tasks, responses

### 6. **Testing Suite** (`test_chandresh.py`, `test_integration_pipeline.py`)
- Comprehensive unit tests
- Integration tests for API endpoints
- End-to-end pipeline flow tests
- Temp database fixtures for isolated testing

### 7. **Reinforcement Learning Agent** (`rl_agent.py`)
- Simple RL agent for adjusting AI assistant behavior
- Processes user feedback to improve performance
- Adjusts component weights based on feedback patterns
- Provides recommendations for improvement

### 8. **Visualization Module** (`visualization.py`)
- Generates visual representations of metrics
- Creates feedback trend and distribution charts
- Produces performance metrics visualizations
- Provides learning curve analysis

### 9. **Demo Frontend** (`demo_frontend.py`)
- Streamlit-based user interface
- Demonstrates full pipeline functionality
- Provides metrics visualization dashboard
- Enables real-time feedback submission

## Documentation

### API Documentation
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API contracts and usage examples
- [SCHEMA_DIAGRAMS.md](SCHEMA_DIAGRAMS.md) - Database schema and system architecture diagrams

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Note: You may need to install additional dependencies for visualization:
```bash
pip install matplotlib seaborn pandas
```

### 2. Initialize Database
```bash
python database.py
```

### 3. Generate Demo Data
```bash
python demo_data.py
```

### 4. Build Initial Embeddings
```bash
python rebuild_embeddings.py
```

### 5. Start API Servers
```bash
# Start Chandresh's EmbedCore & Recall API
uvicorn api_chandresh:app --reload --port 8000

# Start Pipeline API (in a separate terminal)
uvicorn api_pipeline:app --reload --port 8001
```

### 6. Start Demo Frontend (Optional)
```bash
streamlit run demo_frontend.py
```

### 7. Test the APIs
```bash
# Search by message text
curl -X POST "http://localhost:8000/api/search_similar" \
  -H "Content-Type: application/json" \
  -d '{"message_text": "hotel booking", "top_k": 3}'

# Summarize a message
curl -X POST "http://localhost:8001/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{"message_text": "I need help with my hotel booking", "user_id": "user123"}'

# Get embedding statistics
curl "http://localhost:8000/api/embeddings/stats"
```

## API Contract

### POST /api/search_similar

**Input:**
```json
{
  "summary_id": "s123",     // Optional: search by summary ID
  "message_text": "...",    // Optional: search by text
  "top_k": 3               // Optional: number of results (default: 3)
}
```

**Output:**
```json
{
  "related": [
    {
      "item_type": "summary",
      "item_id": "s456", 
      "score": 0.87,
      "text": "Related summary text..."
    }
  ],
  "query_type": "message_text",
  "total_found": 1
}
```

### POST /api/summarize

**Input:**
```json
{
  "message_text": "User message text...",
  "user_id": "user123"      // Optional
}
```

**Output:**
```json
{
  "summary_id": "s123",
  "summary_text": "Generated summary...",
  "confidence_score": 0.95,
  "timestamp": "2023-01-01T12:00:00"
}
```

## Integration Points

### With Seeya (Summarizer)
- Hook into `/api/summarize` to auto-store embeddings
- Monitor summaries table for new entries
- Call `embedding_service.store_embedding()` for new summaries

### With Sankalp (Task Engine)
- Hook into `/api/process_summary` for task generation
- Store embeddings for generated tasks
- Provide context through similarity search

### With Noopur (Response Generator)
- Provide similar context for response generation
- Store embeddings for generated responses
- Enable contextual assistance display

### With Parth (Coach Feedback)
- Collect feedback through `/api/feedback` endpoint
- Store feedback for RL agent training
- Enable behavior adjustment over time

### With Nilesh (Metrics)
- Log metrics for all pipeline operations
- Provide performance data through `/api/metrics/summary`
- Enable monitoring and alerting

### With Streamlit UI
- Provides "Related Past Context" data
- Returns formatted similarity results
- Enables contextual assistance display

## Command Line Tools

### Rebuild Embeddings
```bash
# Rebuild all embeddings
python rebuild_embeddings.py

# Rebuild only summaries
python rebuild_embeddings.py --types summary

# Clear and rebuild
python rebuild_embeddings.py --clear

# Use different model
python rebuild_embeddings.py --model all-mpnet-base-v2

# Verify only (no rebuild)
python rebuild_embeddings.py --verify-only
```

### Run Tests
```bash
# Run all tests
pytest test_chandresh.py test_integration_pipeline.py -v

# Run specific test
pytest test_chandresh.py::TestEmbeddingService::test_generate_embedding -v

# Run integration tests
pytest test_integration_pipeline.py -v
```

## Database Schema

### embeddings
```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,           -- 'summary', 'task', 'response'
    item_id TEXT NOT NULL,             -- Reference to source item
    vector_blob TEXT NOT NULL,         -- JSON-encoded embedding vector
    timestamp TEXT NOT NULL,           -- When embedding was created
    UNIQUE(item_type, item_id)
);
```

### summaries
```sql
CREATE TABLE summaries (
    summary_id TEXT PRIMARY KEY,
    user_id TEXT,
    message_text TEXT,
    summary_text TEXT,
    timestamp TEXT
);
```

### tasks
```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    summary_id TEXT,
    user_id TEXT,
    task_text TEXT,
    priority TEXT,
    timestamp TEXT,
    FOREIGN KEY (summary_id) REFERENCES summaries (summary_id)
);
```

### responses
```sql
CREATE TABLE responses (
    response_id TEXT PRIMARY KEY,
    task_id TEXT,
    user_id TEXT,
    response_text TEXT,
    tone TEXT,
    status TEXT,
    timestamp TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
);
```

### coach_feedback
```sql
CREATE TABLE coach_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id TEXT,
    task_id TEXT,
    response_id TEXT,
    score INTEGER,
    comment TEXT,
    timestamp TEXT,
    FOREIGN KEY (summary_id) REFERENCES summaries (summary_id),
    FOREIGN KEY (task_id) REFERENCES tasks (task_id),
    FOREIGN KEY (response_id) REFERENCES responses (response_id)
);
```

## Performance Considerations

1. **Model Loading**: SentenceTransformer loads lazily on first use
2. **Vector Storage**: Embeddings stored as JSON for simplicity
3. **Similarity Search**: In-memory cosine similarity (adequate for sprint scope)
4. **Scalability**: For production, consider vector databases like Pinecone or Weaviate

## Error Handling

- Graceful fallback to random vectors if model fails
- Database transaction rollback on errors
- Comprehensive logging for debugging
- Input validation for API endpoints
- Retry mechanisms with exponential backoff
- Configurable timeout settings

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Embedding Statistics
```bash
curl http://localhost:8000/api/embeddings/stats
```

### Pipeline Metrics
```bash
curl http://localhost:8001/api/metrics/summary
```

### Logs
Check console output for detailed operation logs with timestamps.

## Integration Testing

The system integrates with the full pipeline:
1. **Message** → Summary (Seeya/Chandresh)
2. **Summary** → Task (Sankalp) 
3. **Task** → Response (Noopur)
4. **Any step** → **Search Similar (Chandresh)** ← **YOU ARE HERE**
5. **Response** → Coach Feedback (Parth)
6. **All steps** → Metrics (Nilesh)

## Sprint Timeline

- **Phase A (0.5-8h)**: ✅ Basic embedding storage and placeholder similarity
- **Phase B (8-18h)**: ✅ Full search_similar endpoint with real embeddings
- **Phase C (18-26h)**: ✅ Integration with Seeya's summarize endpoint
- **Phase D (26-32h)**: ✅ Testing, documentation, and bug fixes
- **Extended (32h+)**: ✅ Pipeline API, integration tests, enhanced docs

## Success Criteria

✅ **POST /api/search_similar** returns top-3 related items with similarity scores  
✅ **Embedding storage** works automatically with new summaries  
✅ **Unit tests** pass for embedding and search functionality  
✅ **Integration** with Streamlit for "Related Past Context" display  
✅ **Reindexing script** available for maintenance  
✅ **API documentation** and examples provided  
✅ **Full pipeline flow** with error handling and configuration  
✅ **Integration tests** covering end-to-end scenarios  
✅ **Comprehensive documentation** with schema diagrams  
✅ **RL agent integration** for feedback-driven learning  
✅ **Visualization dashboard** for metrics monitoring  
✅ **Demo frontend** for user interaction  

## Next Steps

1. **Production Optimization**: Consider vector database for scale
2. **Model Tuning**: Fine-tune embeddings for domain-specific performance  
3. **Caching**: Add Redis caching for frequent similarity searches
4. **Advanced Features**: Hybrid search combining semantic + keyword matching
5. **UI Enhancement**: Develop full-featured frontend interface
6. **RL Integration**: Connect feedback loop to actual RL agent

---

**Owner**: Chandresh  
**Sprint**: 32-Hour Integration Push  
**Status**: Enhanced and Complete ✅