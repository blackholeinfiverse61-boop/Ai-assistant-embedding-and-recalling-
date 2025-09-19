from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime
import sqlite3
import uuid

from embedding_service import embedding_service
from rl_agent import rl_agent, start_feedback_processing_loop, get_rl_agent_performance
from visualization import visualizer, generate_dashboard

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Assistant Pipeline API", version="1.0.0")

# Add endpoint for manual RL agent triggering
@app.post("/api/rl/process_feedback")
async def trigger_rl_processing():
    """Manually trigger RL agent feedback processing."""
    try:
        result = start_feedback_processing_loop()
        return {
            "status": "success",
            "message": "RL agent processing completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in RL processing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/rl/performance")
async def get_rl_performance():
    """Get RL agent performance metrics."""
    try:
        performance = get_rl_agent_performance()
        return performance
    except Exception as e:
        logger.error(f"Error getting RL performance: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

class SummarizeRequest(BaseModel):
    """Request model for summarize endpoint."""
    message_text: str
    user_id: Optional[str] = None

class SummarizeResponse(BaseModel):
    """Response model for summarize endpoint."""
    summary_id: str
    summary_text: str
    confidence_score: float
    timestamp: str

class ProcessSummaryRequest(BaseModel):
    """Request model for process_summary endpoint."""
    summary_id: str
    user_id: Optional[str] = None

class ProcessSummaryResponse(BaseModel):
    """Response model for process_summary endpoint."""
    task_id: str
    task_text: str
    priority: str
    confidence_score: float
    timestamp: str

class FeedbackRequest(BaseModel):
    """Request model for feedback endpoint."""
    summary_id: str
    task_id: Optional[str] = None
    response_id: Optional[str] = None
    score: int  # 1 for thumbs up, -1 for thumbs down
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    """Response model for feedback endpoint."""
    status: str
    message: str
    timestamp: str
    rl_agent_triggered: bool = False

class PipelineConfig(BaseModel):
    """Configuration model for pipeline stages."""
    enable_summarization: bool = True
    enable_task_generation: bool = True
    enable_embedding_storage: bool = True
    retry_attempts: int = 3
    timeout_seconds: int = 30

# Global pipeline configuration
pipeline_config = PipelineConfig()

@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_message(request: SummarizeRequest):
    """
    Summarize a user message and store in database.
    
    Input: { "message_text": "User message...", "user_id": "u123" }
    Output: { "summary_id": "s456", "summary_text": "Summary...", "confidence_score": 0.95 }
    """
    try:
        if not pipeline_config.enable_summarization:
            raise HTTPException(status_code=400, detail="Summarization stage is disabled")
        
        # Generate summary ID
        summary_id = f"s{uuid.uuid4().hex[:6]}"
        
        # In a real implementation, this would call an actual summarization model
        # For now, we'll create a simple summary
        summary_text = f"Summary of: {request.message_text[:50]}..."
        confidence_score = 0.85  # Placeholder confidence score
        
        # Store in database
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO summaries 
            (summary_id, user_id, message_text, summary_text, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (summary_id, request.user_id or "default_user", request.message_text, summary_text, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Store embedding if enabled
        if pipeline_config.enable_embedding_storage:
            embedding_service.store_embedding("summary", summary_id, summary_text)
        
        logger.info(f"Generated summary {summary_id} for user {request.user_id}")
        
        return SummarizeResponse(
            summary_id=summary_id,
            summary_text=summary_text,
            confidence_score=confidence_score,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in summarize_message: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/process_summary", response_model=ProcessSummaryResponse)
async def process_summary(request: ProcessSummaryRequest):
    """
    Process a summary to generate tasks.
    
    Input: { "summary_id": "s123", "user_id": "u123" }
    Output: { "task_id": "t456", "task_text": "Task...", "priority": "medium", "confidence_score": 0.92 }
    """
    try:
        if not pipeline_config.enable_task_generation:
            raise HTTPException(status_code=400, detail="Task generation stage is disabled")
        
        # Retrieve summary from database
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute('SELECT summary_text FROM summaries WHERE summary_id = ?', (request.summary_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Summary {request.summary_id} not found")
        
        summary_text = result[0]
        conn.close()
        
        # Generate task ID
        task_id = f"t{uuid.uuid4().hex[:6]}"
        
        # In a real implementation, this would call an actual task generation model
        # For now, we'll create a simple task based on the summary
        task_text = f"Action item based on: {summary_text[:30]}..."
        priority = "medium"  # Could be "low", "medium", "high"
        confidence_score = 0.80  # Placeholder confidence score
        
        # Store task in database
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            (task_id, summary_id, user_id, task_text, priority, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_id, request.summary_id, request.user_id or "default_user", task_text, priority, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Store embedding if enabled
        if pipeline_config.enable_embedding_storage:
            embedding_service.store_embedding("task", task_id, task_text)
        
        logger.info(f"Generated task {task_id} for summary {request.summary_id}")
        
        return ProcessSummaryResponse(
            task_id=task_id,
            task_text=task_text,
            priority=priority,
            confidence_score=confidence_score,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a summary, task, or response.
    
    Input: { "summary_id": "s123", "task_id": "t456", "score": 1, "comment": "Good response" }
    Output: { "status": "success", "message": "Feedback recorded" }
    """
    try:
        # Validate score
        if request.score not in [-1, 1]:
            raise HTTPException(status_code=400, detail="Score must be either 1 (thumbs up) or -1 (thumbs down)")
        
        # Generate feedback ID
        feedback_id = f"f{uuid.uuid4().hex[:6]}"
        
        # Store feedback in database
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO coach_feedback 
            (id, summary_id, task_id, response_id, score, comment, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback_id,
            request.summary_id,
            request.task_id,
            request.response_id,
            request.score,
            request.comment,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded feedback {feedback_id} with score {request.score}")
        
        # Trigger RL agent processing if we have enough feedback
        rl_agent_triggered = False
        try:
            conn = sqlite3.connect("assistant_demo.db")
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM coach_feedback')
            feedback_count = cursor.fetchone()[0]
            conn.close()
            
            # Trigger RL agent processing every 5 feedback entries
            if feedback_count % 5 == 0 and feedback_count > 0:
                logger.info("Triggering RL agent processing")
                rl_agent.process_feedback_loop()
                rl_agent_triggered = True
        except Exception as e:
            logger.error(f"Error triggering RL agent: {e}")
        
        return FeedbackResponse(
            status="success",
            message="Feedback recorded successfully",
            timestamp=datetime.now().isoformat(),
            rl_agent_triggered=rl_agent_triggered
        )
        
    except Exception as e:
        logger.error(f"Error in submit_feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/pipeline/config", response_model=PipelineConfig)
async def get_pipeline_config():
    """Get current pipeline configuration."""
    return pipeline_config

@app.put("/api/pipeline/config", response_model=PipelineConfig)
async def update_pipeline_config(config: PipelineConfig):
    """Update pipeline configuration."""
    global pipeline_config
    pipeline_config = config
    logger.info("Pipeline configuration updated")
    return pipeline_config

@app.get("/api/metrics/summary")
async def get_pipeline_metrics():
    """Get pipeline metrics and performance data."""
    try:
        conn = sqlite3.connect("assistant_demo.db")
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute('SELECT COUNT(*) FROM summaries')
        summary_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tasks')
        task_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM coach_feedback')
        feedback_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        embedding_count = cursor.fetchone()[0]
        
        # Get feedback statistics
        cursor.execute('SELECT AVG(score) FROM coach_feedback')
        avg_feedback_score = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT score, COUNT(*) FROM coach_feedback GROUP BY score')
        feedback_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        # Get RL agent performance
        rl_performance = get_rl_agent_performance()
        
        return {
            "summaries_processed": summary_count,
            "tasks_generated": task_count,
            "feedback_received": feedback_count,
            "embeddings_stored": embedding_count,
            "average_feedback_score": avg_feedback_score,
            "feedback_distribution": feedback_distribution,
            "rl_agent_performance": rl_performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "pipeline_service", "owner": "chandresh"}

# Add visualization endpoints
@app.get("/api/visualizations/dashboard")
async def get_visualization_dashboard():
    """Get a complete dashboard of visualizations."""
    try:
        dashboard = generate_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"Error generating visualization dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/visualizations/feedback_trend")
async def get_feedback_trend_plot():
    """Get feedback trend visualization."""
    try:
        plot_data = visualizer.plot_feedback_trend(
            visualizer.get_metrics_data().get('feedback', [])
        )
        return {"image": plot_data}
    except Exception as e:
        logger.error(f"Error generating feedback trend plot: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/visualizations/feedback_distribution")
async def get_feedback_distribution_plot():
    """Get feedback distribution visualization."""
    try:
        plot_data = visualizer.plot_feedback_distribution(
            visualizer.get_metrics_data().get('feedback', [])
        )
        return {"image": plot_data}
    except Exception as e:
        logger.error(f"Error generating feedback distribution plot: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/visualizations/performance_metrics")
async def get_performance_metrics_plot():
    """Get performance metrics visualization."""
    try:
        plot_data = visualizer.plot_performance_metrics(
            visualizer.get_metrics_data().get('metrics', [])
        )
        return {"image": plot_data}
    except Exception as e:
        logger.error(f"Error generating performance metrics plot: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/visualizations/confidence_scores")
async def get_confidence_scores_plot():
    """Get confidence scores visualization."""
    try:
        plot_data = visualizer.plot_confidence_scores(
            visualizer.get_metrics_data().get('summaries', [])
        )
        return {"image": plot_data}
    except Exception as e:
        logger.error(f"Error generating confidence scores plot: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/visualizations/learning_curve")
async def get_learning_curve_plot():
    """Get learning curve visualization."""
    try:
        plot_data = visualizer.plot_learning_curve(
            visualizer.get_metrics_data().get('feedback', [])
        )
        return {"image": plot_data}
    except Exception as e:
        logger.error(f"Error generating learning curve plot: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)