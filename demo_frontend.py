#!/usr/bin/env python3
"""
Demo Frontend for AI Assistant Pipeline

This Streamlit app provides a user interface to interact with the AI Assistant pipeline,
including message processing, feedback submission, and metrics visualization.
"""

import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime

# Configuration
PIPELINE_API_URL = "http://localhost:8001"
CHANDRESH_API_URL = "http://localhost:8000"

def main():
    st.set_page_config(
        page_title="AI Assistant Demo",
        page_icon="🤖",
        layout="wide"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stApp {
            background-color: #f0f2f6;
        }
        .header {
            background-color: #4f8bf9;
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .feedback-positive {
            background-color: #d4edda;
            border-left: 5px solid #28a745;
            padding: 1rem;
            margin: 1rem 0;
        }
        .feedback-negative {
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
            padding: 1rem;
            margin: 1rem 0;
        }
        .similar-item {
            background-color: #e9ecef;
            padding: 0.5rem;
            border-radius: 5px;
            margin-bottom: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("<div class='header'><h1>🤖 AI Assistant Pipeline Demo</h1></div>", unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "Message Processing",
        "Pipeline Metrics",
        "Similar Context",
        "Configuration",
        "Visualizations"
    ])
    
    if page == "Message Processing":
        message_processing_page()
    elif page == "Pipeline Metrics":
        pipeline_metrics_page()
    elif page == "Similar Context":
        similar_context_page()
    elif page == "Configuration":
        configuration_page()
    elif page == "Visualizations":
        visualizations_page()

def message_processing_page():
    st.header("💬 Message Processing Pipeline")
    
    # User input
    st.subheader("Enter your message")
    user_message = st.text_area("Type your message here:", height=100)
    user_id = st.text_input("User ID (optional):", value="demo_user")
    
    if st.button("Process Message", type="primary"):
        if user_message:
            with st.spinner("Processing your message..."):
                try:
                    # Step 1: Summarize the message
                    st.subheader("Step 1: Message Summary")
                    summary_response = requests.post(
                        f"{PIPELINE_API_URL}/api/summarize",
                        json={
                            "message_text": user_message,
                            "user_id": user_id
                        }
                    )
                    
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        st.success("✅ Message summarized successfully!")
                        st.json(summary_data)
                        
                        summary_id = summary_data["summary_id"]
                        
                        # Step 2: Generate tasks
                        st.subheader("Step 2: Task Generation")
                        task_response = requests.post(
                            f"{PIPELINE_API_URL}/api/process_summary",
                            json={
                                "summary_id": summary_id,
                                "user_id": user_id
                            }
                        )
                        
                        if task_response.status_code == 200:
                            task_data = task_response.json()
                            st.success("✅ Tasks generated successfully!")
                            st.json(task_data)
                            
                            task_id = task_data["task_id"]
                            
                            # Store for feedback
                            st.session_state.last_summary_id = summary_id
                            st.session_state.last_task_id = task_id
                            
                        else:
                            st.error(f"❌ Task generation failed: {task_response.text}")
                    else:
                        st.error(f"❌ Summarization failed: {summary_response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to API server. Make sure the servers are running.")
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
        else:
            st.warning("Please enter a message to process.")
    
    # Feedback section
    st.markdown("---")
    st.subheader("👍👎 Provide Feedback")
    
    if "last_summary_id" in st.session_state and "last_task_id" in st.session_state:
        st.info(f"Last processed: Summary {st.session_state.last_summary_id}, Task {st.session_state.last_task_id}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👍 Thumbs Up", type="secondary"):
                submit_feedback(1, "Great response!")
        
        with col2:
            if st.button("👎 Thumbs Down", type="secondary"):
                submit_feedback(-1, "Could be improved.")
        
        feedback_comment = st.text_area("Additional feedback (optional):")
        if st.button("Submit Detailed Feedback"):
            if feedback_comment:
                submit_feedback(0, feedback_comment)  # 0 for neutral with comment
            else:
                st.warning("Please enter feedback comment.")
    else:
        st.info("Process a message first to provide feedback.")

def submit_feedback(score, comment):
    """Submit feedback to the pipeline API."""
    try:
        feedback_data = {
            "summary_id": st.session_state.get("last_summary_id", ""),
            "task_id": st.session_state.get("last_task_id", ""),
            "score": score if score in [-1, 1] else 0,
            "comment": comment
        }
        
        response = requests.post(
            f"{PIPELINE_API_URL}/api/feedback",
            json=feedback_data
        )
        
        if response.status_code == 200:
            st.success("✅ Feedback submitted successfully!")
            if response.json().get("rl_agent_triggered"):
                st.info("🤖 RL agent was triggered to process feedback!")
        else:
            st.error(f"❌ Feedback submission failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to API server.")
    except Exception as e:
        st.error(f"❌ Error submitting feedback: {str(e)}")

def pipeline_metrics_page():
    st.header("📊 Pipeline Metrics")
    
    if st.button("Refresh Metrics"):
        try:
            # Get pipeline metrics
            metrics_response = requests.get(f"{PIPELINE_API_URL}/api/metrics/summary")
            
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Summaries Processed", metrics_data["summaries_processed"])
                
                with col2:
                    st.metric("Tasks Generated", metrics_data["tasks_generated"])
                
                with col3:
                    st.metric("Feedback Received", metrics_data["feedback_received"])
                
                with col4:
                    st.metric("Embeddings Stored", metrics_data["embeddings_stored"])
                
                # Feedback statistics
                st.subheader("Feedback Statistics")
                avg_score = metrics_data["average_feedback_score"]
                score_color = "green" if avg_score > 0 else "red" if avg_score < 0 else "gray"
                
                st.markdown(f"""
                <div style="font-size: 24px; font-weight: bold; color: {score_color};">
                    Average Feedback Score: {avg_score:.2f}
                </div>
                """, unsafe_allow_html=True)
                
                # Feedback distribution
                if metrics_data["feedback_distribution"]:
                    st.write("Feedback Distribution:")
                    for score, count in metrics_data["feedback_distribution"].items():
                        st.progress(count / max(metrics_data["feedback_distribution"].values()))
                        st.write(f"Score {score}: {count} responses")
                
                # RL Agent Performance
                if "rl_agent_performance" in metrics_data:
                    st.subheader("RL Agent Performance")
                    rl_perf = metrics_data["rl_agent_performance"]
                    if "current_weights" in rl_perf:
                        st.write("Component Weights:")
                        for component, weight in rl_perf["current_weights"].items():
                            st.progress(weight)
                            st.write(f"{component}: {weight:.2f}")
            
            else:
                st.error(f"❌ Failed to fetch metrics: {metrics_response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to API server.")
        except Exception as e:
            st.error(f"❌ Error fetching metrics: {str(e)}")

def similar_context_page():
    st.header("🔍 Similar Context Search")
    
    st.subheader("Search by Message Text")
    search_text = st.text_input("Enter text to find similar contexts:")
    top_k = st.slider("Number of results", 1, 10, 3)
    
    if st.button("Search Similar Contexts"):
        if search_text:
            try:
                response = requests.post(
                    f"{CHANDRESH_API_URL}/api/search_similar",
                    json={
                        "message_text": search_text,
                        "top_k": top_k
                    }
                )
                
                if response.status_code == 200:
                    search_results = response.json()
                    st.success(f"Found {search_results['total_found']} similar items!")
                    
                    for item in search_results["related"]:
                        st.markdown(f"""
                        <div class="similar-item">
                            <strong>{item['item_type'].title()} {item['item_id']}</strong><br>
                            <small>Similarity: {item['score']:.3f}</small><br>
                            <em>{item['text']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ Search failed: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to API server.")
            except Exception as e:
                st.error(f"❌ Error during search: {str(e)}")
        else:
            st.warning("Please enter search text.")
    
    st.markdown("---")
    
    st.subheader("Search by Summary ID")
    summary_id = st.text_input("Enter summary ID:")
    
    if st.button("Find Similar by Summary ID"):
        if summary_id:
            try:
                response = requests.post(
                    f"{CHANDRESH_API_URL}/api/search_similar",
                    json={
                        "summary_id": summary_id,
                        "top_k": top_k
                    }
                )
                
                if response.status_code == 200:
                    search_results = response.json()
                    st.success(f"Found {search_results['total_found']} similar items!")
                    
                    for item in search_results["related"]:
                        st.markdown(f"""
                        <div class="similar-item">
                            <strong>{item['item_type'].title()} {item['item_id']}</strong><br>
                            <small>Similarity: {item['score']:.3f}</small><br>
                            <em>{item['text']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ Search failed: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to API server.")
            except Exception as e:
                st.error(f"❌ Error during search: {str(e)}")
        else:
            st.warning("Please enter a summary ID.")

def configuration_page():
    st.header("⚙️ Pipeline Configuration")
    
    try:
        # Get current configuration
        config_response = requests.get(f"{PIPELINE_API_URL}/api/pipeline/config")
        
        if config_response.status_code == 200:
            config_data = config_response.json()
            
            st.subheader("Current Configuration")
            
            enable_summarization = st.checkbox(
                "Enable Summarization", 
                value=config_data.get("enable_summarization", True)
            )
            
            enable_task_generation = st.checkbox(
                "Enable Task Generation", 
                value=config_data.get("enable_task_generation", True)
            )
            
            enable_embedding_storage = st.checkbox(
                "Enable Embedding Storage", 
                value=config_data.get("enable_embedding_storage", True)
            )
            
            retry_attempts = st.slider(
                "Retry Attempts", 
                1, 10, 
                config_data.get("retry_attempts", 3)
            )
            
            timeout_seconds = st.slider(
                "Timeout (seconds)", 
                5, 120, 
                config_data.get("timeout_seconds", 30)
            )
            
            if st.button("Update Configuration"):
                new_config = {
                    "enable_summarization": enable_summarization,
                    "enable_task_generation": enable_task_generation,
                    "enable_embedding_storage": enable_embedding_storage,
                    "retry_attempts": retry_attempts,
                    "timeout_seconds": timeout_seconds
                }
                
                update_response = requests.put(
                    f"{PIPELINE_API_URL}/api/pipeline/config",
                    json=new_config
                )
                
                if update_response.status_code == 200:
                    st.success("✅ Configuration updated successfully!")
                else:
                    st.error(f"❌ Failed to update configuration: {update_response.text}")
        
        else:
            st.error(f"❌ Failed to fetch configuration: {config_response.text}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to API server.")
    except Exception as e:
        st.error(f"❌ Error managing configuration: {str(e)}")
    
    st.markdown("---")
    
    st.subheader("RL Agent Controls")
    
    if st.button("Trigger RL Agent Processing"):
        try:
            rl_response = requests.post(f"{PIPELINE_API_URL}/api/rl/process_feedback")
            
            if rl_response.status_code == 200:
                st.success("✅ RL agent processing triggered!")
                rl_result = rl_response.json()
                st.json(rl_result)
            else:
                st.error(f"❌ Failed to trigger RL agent: {rl_response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to API server.")
        except Exception as e:
            st.error(f"❌ Error triggering RL agent: {str(e)}")
    
    if st.button("Get RL Agent Performance"):
        try:
            perf_response = requests.get(f"{PIPELINE_API_URL}/api/rl/performance")
            
            if perf_response.status_code == 200:
                perf_data = perf_response.json()
                st.write("RL Agent Performance:")
                st.json(perf_data)
            else:
                st.error(f"❌ Failed to get RL agent performance: {perf_response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to API server.")
        except Exception as e:
            st.error(f"❌ Error getting RL agent performance: {str(e)}")

def visualizations_page():
    st.header("📈 Metrics Visualizations")
    
    if st.button("Generate Dashboard"):
        try:
            # Get visualization dashboard
            viz_response = requests.get(f"{PIPELINE_API_URL}/api/visualizations/dashboard")
            
            if viz_response.status_code == 200:
                viz_data = viz_response.json()
                
                # Display visualizations
                cols = st.columns(2)
                
                with cols[0]:
                    st.subheader("Feedback Trend")
                    if "feedback_trend" in viz_data and viz_data["feedback_trend"]:
                        st.image(
                            f"data:image/png;base64,{viz_data['feedback_trend']}",
                            caption="Cumulative Feedback Trend",
                            use_column_width=True
                        )
                
                with cols[1]:
                    st.subheader("Feedback Distribution")
                    if "feedback_distribution" in viz_data and viz_data["feedback_distribution"]:
                        st.image(
                            f"data:image/png;base64,{viz_data['feedback_distribution']}",
                            caption="Feedback Score Distribution",
                            use_column_width=True
                        )
                
                cols2 = st.columns(2)
                
                with cols2[0]:
                    st.subheader("Performance Metrics")
                    if "performance_metrics" in viz_data and viz_data["performance_metrics"]:
                        st.image(
                            f"data:image/png;base64,{viz_data['performance_metrics']}",
                            caption="API Performance Metrics",
                            use_column_width=True
                        )
                
                with cols2[1]:
                    st.subheader("Learning Curve")
                    if "learning_curve" in viz_data and viz_data["learning_curve"]:
                        st.image(
                            f"data:image/png;base64,{viz_data['learning_curve']}",
                            caption="Learning Curve",
                            use_column_width=True
                        )
                
            else:
                st.error(f"❌ Failed to generate dashboard: {viz_response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to API server.")
        except Exception as e:
            st.error(f"❌ Error generating dashboard: {str(e)}")

if __name__ == "__main__":
    main()