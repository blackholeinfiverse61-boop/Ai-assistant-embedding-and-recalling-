#!/usr/bin/env python3
"""
Visualization Module for AI Assistant Metrics and Confidence Scoring

This module provides functions to generate visual representations of metrics,
confidence scores, and learning curves for the AI assistant system.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import io
import base64
from matplotlib.axes import Axes
plt.switch_backend('Agg')  # Use non-interactive backend

class MetricsVisualizer:
    """Visualizer for AI assistant metrics and confidence scoring."""
    
    def __init__(self, db_path: str = "assistant_demo.db"):
        self.db_path = db_path
        # Set up styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def get_metrics_data(self) -> Dict:
        """Retrieve metrics data from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get feedback data with timestamps
            cursor.execute('''
                SELECT score, timestamp 
                FROM coach_feedback 
                ORDER BY timestamp
            ''')
            feedback_data = cursor.fetchall()
            
            # Get metrics data
            cursor.execute('''
                SELECT endpoint, status_code, latency_ms, timestamp
                FROM metrics
                ORDER BY timestamp
            ''')
            metrics_data = cursor.fetchall()
            
            # Get summary confidence scores
            cursor.execute('''
                SELECT summary_id, 
                       LENGTH(summary_text) as summary_length,
                       timestamp
                FROM summaries
                ORDER BY timestamp
            ''')
            summary_data = cursor.fetchall()
            
            conn.close()
            
            return {
                'feedback': feedback_data,
                'metrics': metrics_data,
                'summaries': summary_data
            }
            
        except Exception as e:
            print(f"Error retrieving metrics data: {e}")
            return {}
    
    def plot_feedback_trend(self, feedback_data: List[Tuple]) -> str:
        """Plot feedback trend over time."""
        if not feedback_data:
            return self._create_empty_plot("No feedback data available")
        
        # Convert to DataFrame
        if feedback_data:
            scores, timestamps = zip(*feedback_data) if feedback_data else ([], [])
            df = pd.DataFrame({'score': scores, 'timestamp': timestamps})
        else:
            df = pd.DataFrame({'score': [], 'timestamp': []})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate cumulative scores
        df['cumulative_score'] = df['score'].cumsum()
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df['timestamp'], df['cumulative_score'], marker='o', linewidth=2, markersize=4)
        ax.set_title('Cumulative Feedback Trend Over Time', fontsize=14, pad=20)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Cumulative Feedback Score', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add horizontal line at zero
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=1)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_feedback_distribution(self, feedback_data: List[Tuple]) -> str:
        """Plot feedback score distribution."""
        if not feedback_data:
            return self._create_empty_plot("No feedback data available")
        
        # Convert to DataFrame
        if feedback_data:
            scores, timestamps = zip(*feedback_data) if feedback_data else ([], [])
            df = pd.DataFrame({'score': scores, 'timestamp': timestamps})
        else:
            df = pd.DataFrame({'score': [], 'timestamp': []})
        
        # Create plot
        fig, ax = plt.subplots(figsize=(8, 6))
        score_counts = df['score'].value_counts().sort_index()
        # Convert to lists to avoid type checking issues
        x_values = list(score_counts.index)
        y_values = list(score_counts.values)
        bars = ax.bar(x_values, y_values, color=['#ff6b6b', '#4ecdc4'])
        ax.set_title('Feedback Score Distribution', fontsize=14, pad=20)
        ax.set_xlabel('Score', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_performance_metrics(self, metrics_data: List[Tuple]) -> str:
        """Plot performance metrics including latency and error rates."""
        if not metrics_data:
            return self._create_empty_plot("No metrics data available")
        
        # Convert to DataFrame
        if metrics_data:
            endpoints, status_codes, latency_ms, timestamps = zip(*metrics_data) if metrics_data else ([], [], [], [])
            df = pd.DataFrame({
                'endpoint': endpoints,
                'status_code': status_codes,
                'latency_ms': latency_ms,
                'timestamp': timestamps
            })
        else:
            df = pd.DataFrame({
                'endpoint': [],
                'status_code': [],
                'latency_ms': [],
                'timestamp': []
            })
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Create subplot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Latency over time
        ax1.plot(df['timestamp'], df['latency_ms'], marker='o', linewidth=1, markersize=3)
        ax1.set_title('API Response Latency Over Time', fontsize=14, pad=20)
        ax1.set_ylabel('Latency (ms)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Error rate over time (status codes >= 400)
        df['is_error'] = df['status_code'] >= 400
        df['error_rate'] = df['is_error'].rolling(window=10, min_periods=1).mean() * 100
        
        ax2.plot(df['timestamp'], df['error_rate'], color='red', linewidth=2)
        ax2.set_title('Error Rate Over Time (Rolling 10-point average)', fontsize=14, pad=20)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Error Rate (%)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_confidence_scores(self, summary_data: List[Tuple]) -> str:
        """Plot confidence scores and summary quality metrics."""
        if not summary_data:
            return self._create_empty_plot("No summary data available")
        
        # Convert to DataFrame
        if summary_data:
            summary_ids, summary_lengths, timestamps = zip(*summary_data) if summary_data else ([], [], [])
            df = pd.DataFrame({
                'summary_id': summary_ids,
                'summary_length': summary_lengths,
                'timestamp': timestamps
            })
        else:
            df = pd.DataFrame({
                'summary_id': [],
                'summary_length': [],
                'timestamp': []
            })
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(df['timestamp'], df['summary_length'], alpha=0.7, s=60)
        ax.set_title('Summary Length Over Time', fontsize=14, pad=20)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Summary Length (characters)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def plot_learning_curve(self, feedback_data: List[Tuple]) -> str:
        """Plot learning curve based on feedback trends."""
        if not feedback_data:
            return self._create_empty_plot("No feedback data available")
        
        # Convert to DataFrame
        if feedback_data:
            scores, timestamps = zip(*feedback_data) if feedback_data else ([], [])
            df = pd.DataFrame({'score': scores, 'timestamp': timestamps})
        else:
            df = pd.DataFrame({'score': [], 'timestamp': []})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate moving average of feedback scores
        df['moving_avg'] = df['score'].rolling(window=5, min_periods=1).mean()
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df['timestamp'], df['moving_avg'], linewidth=2, color='#6c5ce7')
        ax.set_title('Learning Curve (5-point Moving Average of Feedback)', fontsize=14, pad=20)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Average Feedback Score', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add horizontal line at zero
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=1)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def create_dashboard(self) -> Dict[str, str]:
        """Create a complete dashboard with all visualizations."""
        # Get data
        data = self.get_metrics_data()
        
        # Create visualizations
        dashboard = {
            'feedback_trend': self.plot_feedback_trend(data.get('feedback', [])),
            'feedback_distribution': self.plot_feedback_distribution(data.get('feedback', [])),
            'performance_metrics': self.plot_performance_metrics(data.get('metrics', [])),
            'confidence_scores': self.plot_confidence_scores(data.get('summaries', [])),
            'learning_curve': self.plot_learning_curve(data.get('feedback', []))
        }
        
        return dashboard
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 encoded string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_str
    
    def _create_empty_plot(self, message: str) -> str:
        """Create an empty plot with a message."""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', transform=ax.transAxes, 
                fontsize=14, wrap=True)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return self._fig_to_base64(fig)

# Global visualizer instance
visualizer = MetricsVisualizer()

def generate_dashboard():
    """Generate a complete metrics dashboard."""
    try:
        return visualizer.create_dashboard()
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        return {}

def generate_feedback_trend_plot():
    """Generate feedback trend plot."""
    try:
        data = visualizer.get_metrics_data()
        return visualizer.plot_feedback_trend(data.get('feedback', []))
    except Exception as e:
        print(f"Error generating feedback trend plot: {e}")
        return ""

def generate_feedback_distribution_plot():
    """Generate feedback distribution plot."""
    try:
        data = visualizer.get_metrics_data()
        return visualizer.plot_feedback_distribution(data.get('feedback', []))
    except Exception as e:
        print(f"Error generating feedback distribution plot: {e}")
        return ""

if __name__ == "__main__":
    # Generate sample dashboard
    dashboard = generate_dashboard()
    print(f"Generated {len(dashboard)} visualizations")
    
    # Save sample plot to file for testing
    if dashboard.get('feedback_trend'):
        import base64
        img_data = base64.b64decode(dashboard['feedback_trend'])
        with open('sample_feedback_trend.png', 'wb') as f:
            f.write(img_data)
        print("Sample feedback trend plot saved as 'sample_feedback_trend.png'")