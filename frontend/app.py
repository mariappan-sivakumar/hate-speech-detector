import streamlit as st
import requests
import pandas as pd
import io

# Setup page configurations
st.set_page_config(
    page_title="🛡️ Hate Speech Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Injected CSS for modern design and custom typography
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Apply typography globally */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header Container styling with premium gradient */
    .header-container {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 3rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        margin-bottom: 2.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
    }
    
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        font-size: 1.25rem;
        font-weight: 300;
        opacity: 0.95;
    }
    
    /* Metrics container */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.25);
    }

    /* Force text visibility inside metrics */
    div[data-testid="stMetric"] label, 
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] > div {
        color: #94a3b8 !important; /* Soft light gray for labels */
        font-weight: 500;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] > div {
        color: #ffffff !important; /* Crisp white for values */
        font-weight: 700;
    }
    
    /* Buttons custom shadow and hover transitions */
    .stButton>button {
        background: linear-gradient(135deg, #1f4068 0%, #162447 100%);
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(22, 36, 71, 0.2) !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #162447 0%, #1f4068 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(22, 36, 71, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown("""
<div class="header-container">
    <div class="header-title">🛡️ Hate Speech Detector</div>
    <div class="header-subtitle">Paste YouTube comments below to analyze sentiment, confidence, type, and reasoning using Google Gemini API</div>
</div>
""", unsafe_allow_html=True)

BACKEND_URL = "http://localhost:8080/api"

# Initialize Session State
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# Section 1 - INPUT
st.markdown("### 📥 Enter Comments")
raw_input = st.text_area(
    "Paste one comment per line (Minimum 1, Maximum 100 comments):",
    height=200,
    placeholder="Example:\nPeople like you should not be allowed to speak publicly. Go back to where you came from.\nGood video but too lengthy.\nI will find you and make you regret posting this."
)

analyze_button = st.button("🔍 Analyze Comments")

# Split and clean comments
comments_list = [line.strip() for line in raw_input.split("\n") if line.strip()]

if analyze_button:
    if not comments_list:
        st.warning("⚠️ Input is empty. Please enter at least one comment to analyze.")
    elif len(comments_list) > 100:
        st.error("⚠️ Maximum comments exceeded. Please submit a maximum of 100 comments at a time.")
    else:
        with st.spinner("Analyzing comments with Google Gemini..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/classify",
                    json={"comments": comments_list},
                    timeout=60
                )
                if response.status_code == 200:
                    st.session_state.analysis_results = response.json()
                    st.toast("✅ Analysis completed successfully!")
                elif response.status_code == 422:
                    st.error(f"Validation Error (HTTP 422): The API validation failed. Details: {response.json()}")
                else:
                    st.error(f"Error (HTTP {response.status_code}): {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection Error: Unable to reach the FastAPI backend at http://localhost:8000. Please check if the backend is running.")
            except Exception as e:
                st.error(f"❌ Unexpected Error: {str(e)}")

# Display Results if available
if st.session_state.analysis_results is not None:
    data = st.session_state.analysis_results
    
    st.markdown("---")
    
    # Section 2 - SUMMARY CARDS
    st.markdown("### 📊 Analysis Summary")
    total_comments = data["total"]
    hate_count = data["hate_speech_count"]
    hate_percentage = (hate_count / total_comments * 100) if total_comments > 0 else 0.0
    
    m_col1, m_col2, m_col3 = st.columns(3)
    
    with m_col1:
        st.metric(label="Total Comments", value=total_comments)
    with m_col2:
        st.metric(label="Hate Speech Detected", value=hate_count)
    with m_col3:
        st.metric(label="Hate Speech Percentage", value=f"{hate_percentage:.1f}%")
        
    st.markdown("---")
    
    # Section 3 - RESULTS TABLE
    st.markdown("### 📋 Classification Details")
    
    results_records = []
    for item in data["results"]:
        results_records.append({
            "Comment": item["comment"],
            "Label": item["label"],
            "Confidence": item["confidence"],
            "Type": item["type"],
            "Reason": item["reason"]
        })
        
    df = pd.DataFrame(results_records)
    
    # Styling function for dataframe cells
    def color_label(val):
        if val == "Hate Speech":
            # Soft dark-red / pastel red style
            return "background-color: #ffebee; color: #c62828; font-weight: bold;"
        elif val == "No Hate Speech":
            # Soft dark-green / pastel green style
            return "background-color: #e8f5e9; color: #2e7d32; font-weight: bold;"
        return ""
    
    try:
        styled_df = df.style.map(color_label, subset=["Label"])
    except AttributeError:
        styled_df = df.style.applymap(color_label, subset=["Label"])
        
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Section 4 - EXPORT
    st.markdown("### 💾 Export Data")
    
    # Prepare CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8")
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_bytes,
        file_name="youtube_hate_speech_analysis.csv",
        mime="text/csv"
    )
