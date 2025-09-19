import os
from typing import Any, Dict, Optional

import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Assistant • Modern Dashboard",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------
# Global styles and assets (fonts, icons, dark theme, gradients, glass cards)
# ----------------------------------
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Poppins:wght@300;500;600;700&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet"/>

<style>
:root{
  --bg0: #0b0f17;
  --bg1: #0f1522;
  --bg2: #121a2b;
  --glass: rgba(255,255,255,0.06);
  --accent: #7c4dff;
  --accent-2: #00e6a7;
  --text: #eff3fb;
  --muted: #a8b3c7;
  --danger: #ff5f6d;
  --warn: #ffb020;
  --success: #00e6a7;
  --card-radius: 16px;
  --shadow-1: 0 10px 30px rgba(0,0,0,0.35);
  --shadow-2: 0 10px 25px rgba(124,77,255,0.25);
}
html, body, [data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 800px at 20% 10%, #10182a 0%, #0b0f17 50%) fixed,
              linear-gradient(160deg, #0b0f17 0%, #10182a 60%, #0f1522 100%) fixed;
  color: var(--text);
  font-family: "Inter", system-ui, -apple-system, Segoe UI, Helvetica, Arial;
  scroll-behavior: smooth;
}
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* Topbar */
.topbar{
  position: sticky; top: 0; z-index: 20;
  backdrop-filter: blur(10px);
  background: linear-gradient(120deg, rgba(16,24,42,0.75), rgba(12,14,20,0.65));
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 14px 18px; border-radius: 14px; margin-bottom: 18px; box-shadow: var(--shadow-1);
}
.topbar .wrap{ display: flex; align-items: center; gap: 18px; justify-content: space-between; }
.brand{ display: flex; align-items: center; gap: 14px; }
.brand .logo{
  width: 40px; height: 40px; border-radius: 12px;
  background: conic-gradient(from 200deg, #7c4dff, #00e6a7, #7c4dff);
  box-shadow: 0 8px 24px rgba(124,77,255,0.35), inset 0 0 25px rgba(0,230,167,0.35);
  position: relative;
}
.brand .logo:before{ content:""; position:absolute; inset:5px; border-radius: 10px; background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.35), transparent 40%); }
.brand h1{ font-family: "Poppins", system-ui, sans-serif; font-weight: 700; font-size: 20px; letter-spacing: 0.4px; margin: 0; }
.brand .tag{ color: var(--muted); font-size: 12px; margin-top: -2px; }

/* Nav */
.nav{ display:flex; gap: 12px; align-items:center; flex-wrap: wrap; }
.nav a{ color: var(--muted); padding: 8px 12px; border-radius: 10px; text-decoration: none; border: 1px solid rgba(255,255,255,0.06); background: rgba(255,255,255,0.02); transition: all .22s ease; }
.nav a:hover{ color: var(--text); border-color: rgba(124,77,255,0.55); box-shadow: var(--shadow-2); transform: translateY(-2px); }
.nav a.active{ color: var(--text); background: linear-gradient(135deg, rgba(124,77,255,0.25), rgba(0,230,167,0.15)); border-color: rgba(124,77,255,0.55); }

/* Hero */
.hero{ padding: 16px 18px 4px; margin-bottom: 10px; }
.hero h2{ font-family: "Poppins", system-ui, sans-serif; font-size: 28px; margin: 0 0 6px; }
.hero .sub{ color: var(--muted); font-size: 14px; }

/* Cards */
.card{ border-radius: var(--card-radius); background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03)); border: 1px solid rgba(255,255,255,0.08); box-shadow: var(--shadow-1); position: relative; overflow: hidden; padding: 18px; transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; }
.card:hover{ transform: translateY(-4px); border-color: rgba(124,77,255,0.5); box-shadow: var(--shadow-2); }
.card .label{ color: var(--muted); font-size: 12px; letter-spacing: .6px; text-transform: uppercase; margin-bottom: 8px; }
.card .value{ font-size: 24px; font-weight: 700; letter-spacing: .3px; }
.card .trend{ margin-top: 8px; font-size: 12px; color: var(--success); }
.card .icon{ position: absolute; top: 14px; right: 14px; color: rgba(255,255,255,0.35); font-size: 18px; }

/* Widget styling */
.stSlider [data-baseweb="slider"]>div{ background: linear-gradient(90deg, rgba(124,77,255,0.65), rgba(0,230,167,0.65)) !important; }
.stSlider [data-baseweb="slider"]>div>div{ box-shadow: 0 0 0 6px rgba(124,77,255,0.25) !important; border: 2px solid rgba(255,255,255,0.2) !important; }
.stSelectbox, .stMultiSelect, .stTextInput, .stTextArea{ border-radius: 12px !important; }
.stButton>button{ background: linear-gradient(135deg, #7c4dff, #00e6a7) !important; color: #0b0f17 !important; border: 0 !important; font-weight: 700 !important; border-radius: 12px !important; padding: 10px 16px !important; box-shadow: 0 10px 24px rgba(124,77,255,0.35); transition: transform .15s ease, box-shadow .15s ease; }
.stButton>button:hover{ transform: translateY(-2px); box-shadow: var(--shadow-2); }

/* Section headings */
.section-title{ display:flex; align-items:center; gap:10px; margin: 14px 0 10px; font-family: "Poppins", system-ui, sans-serif; font-size: 18px; }
.section-title i{ color: var(--accent); }

/* Footer */
.footer{ margin-top: 24px; padding: 18px; border-radius: 14px; background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.footer .links{ display:flex; gap: 12px; align-items:center; flex-wrap: wrap; }
.footer .links a{ color: var(--muted); text-decoration: none; padding: 8px 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); transition: all .22s ease; }
.footer .links a:hover{ color: var(--text); border-color: rgba(124,77,255,0.55); transform: translateY(-2px); }
.footer .copy{ color: var(--muted); font-size: 12px; }

/* Animations */
@keyframes fadeUp { from {opacity:0; transform: translateY(10px);} to {opacity:1; transform: translateY(0);} }
.card, .topbar, .footer, .hero { animation: fadeUp .5s ease both; }

/* Mobile */
@media (max-width: 768px){ .nav { justify-content: flex-start; overflow-x: auto; } .brand h1{ font-size: 18px; } .card .value{ font-size: 22px; } }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------
# Configuration
# ----------------------------------
API_BASE_DEFAULT = os.getenv("API_BASE", "http://127.0.0.1:8000")
st.sidebar.header("Configuration")
api_base = st.sidebar.text_input(
    "API Base URL",
    value=API_BASE_DEFAULT,
    help="Unified FastAPI server base URL (e.g., http://127.0.0.1:8000)",
)

if "last_task_id" not in st.session_state:
    st.session_state.last_task_id = "t123"
if "last_response_id" not in st.session_state:
    st.session_state.last_response_id = None
if "last_summary_id" not in st.session_state:
    st.session_state.last_summary_id = "s1"

# ----------------------------------
# Helpers
# ----------------------------------

def post_json(path: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    url = f"{api_base}{path}"
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_json(path: str, timeout: int = 10) -> Dict[str, Any]:
    url = f"{api_base}{path}"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

# ----------------------------------
# Topbar
# ----------------------------------
st.markdown(
    """
<div class="topbar">
  <div class="wrap">
    <div class="brand">
      <div class="logo"></div>
      <div>
        <h1>AI Assistant</h1>
        <div class="tag">Insightful • Fast • Delightful</div>
      </div>
    </div>
    <div class="nav">
      <a href="#dashboard" class="active"><i class="fa-solid fa-gauge-high"></i> Dashboard</a>
      <a href="#workspace"><i class="fa-solid fa-layer-group"></i> Workspace</a>
      <a href="#analytics"><i class="fa-solid fa-chart-line"></i> Analytics</a>
      <a href="#about"><i class="fa-solid fa-circle-info"></i> About</a>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------------
# Hero + Metrics overview
# ----------------------------------
st.markdown(
    """
<div class="hero" id="dashboard">
  <h2>Welcome back — your AI operations look stellar today.</h2>
  <div class="sub">Track performance, explore insights, and fine-tune the experience — all in one place.</div>
</div>
""",
    unsafe_allow_html=True,
)

# Fetch metrics to populate real values
metrics_data: Dict[str, Any] = {}
try:
    metrics_data = get_json("/api/metrics")
except Exception:
    metrics_data = {
        "api_metrics": {"total_calls": 0, "avg_latency_ms": 0.0, "error_rate": 0.0},
        "total_responses": 0,
        "error_rate": 0.0,
        "avg_latency_ms": 0.0,
    }

api_total_calls = metrics_data.get("api_metrics", {}).get("total_calls", 0)
api_latency = metrics_data.get("avg_latency_ms", metrics_data.get("api_metrics", {}).get("avg_latency_ms", 0.0))
api_error_rate = metrics_data.get("error_rate", metrics_data.get("api_metrics", {}).get("error_rate", 0.0))
api_total_responses = metrics_data.get("total_responses", 0)

# Metric cards row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f"""
        <div class="card">
          <div class="icon"><i class="fa-solid fa-signal"></i></div>
          <div class="label">Total API Calls</div>
          <div class="value">{api_total_calls:,}</div>
          <div class="trend"><i class="fa-solid fa-bolt"></i> Live traffic</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f"""
        <div class="card">
          <div class="icon"><i class="fa-solid fa-gauge"></i></div>
          <div class="label">Avg Latency</div>
          <div class="value">{api_latency:.1f} ms</div>
          <div class="trend" style="color:#00e6a7;"><i class="fa-solid fa-arrow-trend-down"></i> Optimized</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f"""
        <div class="card">
          <div class="icon"><i class="fa-solid fa-shield-halved"></i></div>
          <div class="label">Error Rate</div>
          <div class="value" style="color:#ffb020;">{(api_error_rate*100):.2f}%</div>
          <div class="trend" style="color:#ffb020;"><i class="fa-solid fa-circle-exclamation"></i> Watchlist</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m4:
    st.markdown(
        f"""
        <div class="card">
          <div class="icon"><i class="fa-solid fa-message"></i></div>
          <div class="label">Total Responses</div>
          <div class="value">{api_total_responses:,}</div>
          <div class="trend"><i class="fa-solid fa-arrow-trend-up"></i> Engagement</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------
# Workspace: Respond • Recall • Feedback • Metrics
# ----------------------------------
st.markdown('<div class="section-title" id="workspace"><i class="fa-solid fa-layer-group"></i><span>Workspace</span></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Respond", "Recall", "Feedback", "Metrics"])

# Respond Tab
with tab1:
    cta1, cta2 = st.columns([2, 1])
    with cta1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Generate Response")
        task_id = st.text_input("Task ID", value=st.session_state.last_task_id)
        user_id = st.text_input("User ID", value="u1")
        if st.button("Send Response", type="primary"):
            with st.spinner("Generating response..."):
                try:
                    data = post_json("/api/respond", {"task_id": task_id, "user_id": user_id}, timeout=15)
                    st.success("Response generated!")
                    st.session_state.last_task_id = data.get("task_id", task_id)
                    st.session_state.last_response_id = data.get("response_id")
                    st.json(data)
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with cta2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Seed Embedding")
        with st.form("seed_form"):
            seed_item_type = st.selectbox("Item Type", ["summary", "task"], index=0)
            seed_item_id = st.text_input("Item ID", value="s1")
            seed_text = st.text_area("Text", value="hotel booking confirmation and itinerary")
            submitted = st.form_submit_button("Store Embedding")
            if submitted:
                try:
                    url = f"{api_base}/api/store_embedding"
                    resp = requests.post(url, params={"item_type": seed_item_type, "item_id": seed_item_id, "text": seed_text}, timeout=10)
                    if resp.status_code == 200 and resp.json().get("stored"):
                        st.success("Embedding stored")
                        st.session_state.last_summary_id = seed_item_id if seed_item_type == "summary" else st.session_state.last_summary_id
                    else:
                        st.warning("Store embedding returned unexpected result")
                except Exception as e:
                    st.error(f"Error seeding embedding: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# Recall Tab
with tab2:
    rl1, rl2 = st.columns(2)
    with rl1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Search by Message Text")
        q_text = st.text_area("Message", value="need help booking a hotel")
        top_k = st.slider("Top K", min_value=1, max_value=10, value=3)
        if st.button("Search by Message"):
            with st.spinner("Searching similar..."):
                try:
                    data = post_json("/api/search_similar", {"message_text": q_text, "top_k": top_k})
                    items = data.get("related", [])
                    if not items:
                        st.info("No related items found.")
                    else:
                        for it in items:
                            st.markdown(f"<div class='card' style='margin-top:8px;'><div class='label'>{it['item_type'].title()}</div><div class='value' style='font-size:18px'>{it['item_id']}</div><div class='trend'>Score: {it['score']:.3f}</div></div>", unsafe_allow_html=True)
                except requests.exceptions.RequestException as e:
                    st.error(f"Search failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with rl2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Search by Summary ID")
        sid = st.text_input("Summary ID", value=st.session_state.last_summary_id)
        top_k2 = st.slider("Top K (summary)", min_value=1, max_value=10, value=3, key="topk2")
        if st.button("Search by Summary"):
            with st.spinner("Searching similar..."):
                try:
                    data = post_json("/api/search_similar", {"summary_id": sid, "top_k": top_k2})
                    items = data.get("related", [])
                    if not items:
                        st.info("No related items found.")
                    else:
                        for it in items:
                            st.markdown(f"<div class='card' style='margin-top:8px;'><div class='label'>{it['item_type'].title()}</div><div class='value' style='font-size:18px'>{it['item_id']}</div><div class='trend'>Score: {it['score']:.3f}</div></div>", unsafe_allow_html=True)
                except requests.exceptions.RequestException as e:
                    st.error(f"Search failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# Feedback Tab
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Coach Feedback")
    with st.form("feedback_form"):
        summary_id = st.text_input("Summary ID", value=st.session_state.last_summary_id)
        task_id_fb = st.text_input("Task ID", value=st.session_state.last_task_id)
        response_id = st.text_input("Response ID", value=st.session_state.last_response_id or "")
        st.markdown("Scores")
        c1, c2, c3 = st.columns(3)
        with c1:
            clarity = st.slider("Clarity", 1, 5, 4)
        with c2:
            relevance = st.slider("Relevance", 1, 5, 5)
        with c3:
            tone = st.slider("Tone", 1, 5, 4)
        comment = st.text_area("Comment", value="Well-composed and helpful response.")
        submitted_fb = st.form_submit_button("Submit Feedback")
        if submitted_fb:
            payload = {
                "summary_id": summary_id,
                "task_id": task_id_fb,
                "response_id": response_id,
                "scores": {"clarity": clarity, "relevance": relevance, "tone": tone},
                "comment": comment,
            }
            with st.spinner("Submitting feedback..."):
                try:
                    data = post_json("/api/coach_feedback", payload)
                    st.success(f"Saved feedback {data.get('feedback_id')} with score {data.get('score')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Feedback failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# Metrics Tab
with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Service Metrics")
    if st.button("Refresh Metrics"):
        st.rerun()
    try:
        st.json(metrics_data)
    except Exception as e:
        st.error(f"Failed to load metrics: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------
# Analytics quick section (summary)
# ----------------------------------
st.markdown('<div class="section-title" id="analytics"><i class="fa-solid fa-chart-line"></i><span>Analytics</span></div>', unsafe_allow_html=True)
a1, a2 = st.columns([1.2, 1])
with a1:
    st.markdown(
        """
        <div class="card" style="min-height:240px;">
          <div class="label">Engagement Overview</div>
          <div class="value">Sessions per feature • last 14 days</div>
          <div style="margin-top:10px; color:var(--muted); font-size:13px;">
            Conversations trending positively • Recall usage steadily rising • Feedback interactions healthy
          </div>
          <div style="margin-top:16px; height:8px; width:100%; background:rgba(255,255,255,0.06); border-radius:10px; overflow:hidden;">
            <div style="height:100%; width:72%; background:linear-gradient(90deg, #7c4dff, #00e6a7);"></div>
          </div>
          <div style="margin-top:10px; color:var(--muted); font-size:12px;">Feature adoption at 72% target (↑)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with a2:
    st.markdown(
        """
        <div class="card" style="min-height:240px;">
          <div class="label">Retention Drivers</div>
          <div class="value">Top factors impacting repeat usage</div>
          <ul style="margin-top:12px; color:var(--muted); padding-left:18px; line-height:1.6;">
            <li>Fast end-to-end response time</li>
            <li>Helpful contextual recall in responses</li>
            <li>Clear feedback loop & consistent tone</li>
          </ul>
          <div class="trend"><i class="fa-solid fa-check"></i> Optimized for daily returns</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------
# About / Footer
# ----------------------------------
st.markdown('<div class="section-title" id="about"><i class="fa-solid fa-circle-info"></i><span>About This App</span></div>', unsafe_allow_html=True)
st.markdown(
    """
<div class="card">
  <div class="label">Crafted for Delight</div>
  <div style="color:var(--muted);">
    A modern, polished AI assistant interface focused on performance, clarity, and retention. Designed with a minimalist
    dark aesthetic, smooth interactions, and responsive layouts that feel right at home on any device.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="footer">
  <div class="links">
    <a href="https://github.com" target="_blank"><i class="fa-brands fa-github"></i> GitHub</a>
    <a href="https://twitter.com" target="_blank"><i class="fa-brands fa-x-twitter"></i> X</a>
    <a href="mailto:contact@aiassistant.app"><i class="fa-solid fa-envelope"></i> contact@aiassistant.app</a>
    <a href="https://www.linkedin.com" target="_blank"><i class="fa-brands fa-linkedin"></i> LinkedIn</a>
  </div>
  <div class="copy">© 2025 AI Assistant • Designed for speed, clarity, and delight.</div>
</div>
""",
    unsafe_allow_html=True,
)
