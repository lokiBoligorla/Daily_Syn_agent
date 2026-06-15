import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Add workspace directory to path to ensure imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agent.graph import create_agent_graph
from agent.nodes.email_sender import email_sender_node
from tools.excel_tool import find_excel_file

# Load existing environment variables
load_dotenv()

# Streamlit page configuration
st.set_page_config(
    page_title="DailySync - AI Internship Reporting Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics (Sleek dark theme, glassmorphism, Outfit font)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Typography & Overall Page */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Background gradient */
.stApp {
    background: radial-gradient(circle at top right, #0f172a, #0b0f19);
    color: #f1f5f9;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Titles and Headers */
h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.025em;
}

/* Glowing text */
.title-gradient {
    background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1d4ed8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}

.subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Glassmorphism Cards */
.glass-card {
    background: rgba(30, 41, 59, 0.45);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}

.log-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    font-family: monospace;
    font-size: 0.9rem;
    padding: 15px;
    color: #38bdf8;
    max-height: 250px;
    overflow-y: auto;
    margin-bottom: 15px;
}

/* Custom Gradient Button */
div.stButton > button:first-child {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #1d4ed8 100%);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.4);
    transition: all 0.3s ease;
    width: 100%;
}

div.stButton > button:first-child:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.6);
    background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 50%, #2563eb 100%);
    color: #ffffff;
}

div.stButton > button:first-child:active {
    transform: translateY(1px);
}

/* Secondary Actions */
.send-btn div.stButton > button:first-child {
    background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
    box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.4) !important;
}

.send-btn div.stButton > button:first-child:hover {
    background: linear-gradient(135deg, #34d399 0%, #6ee7b7 100%) !important;
    box-shadow: 0 6px 20px 0 rgba(16, 185, 129, 0.6) !important;
}

/* Tab Active Styles */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    background-color: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px 8px 0px 0px;
    padding: 8px 16px;
    color: #94a3b8;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(59, 130, 246, 0.15) !important;
    border-bottom: 2px solid #3b82f6 !important;
    color: #60a5fa !important;
}

/* Make widget labels bright and readable */
div[data-testid="stWidgetLabel"] p, label, .stWidgetLabel {
    color: #e2e8f0 !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

import json
# Session state initialization & Profile Persistence
DEFAULT_PROFILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "dailysync_profile.json")

# Initialize Cookie Controller for browser-based persistence
try:
    from streamlit_cookies_controller import CookieController
    cookie_controller = CookieController()
except ImportError:
    cookie_controller = None

if "agent_result" not in st.session_state:
    st.session_state.agent_result = None
if "processing" not in st.session_state:
    st.session_state.processing = False

if "profile_loaded" not in st.session_state:
    profile = {}
    
    # 1. Try to load from browser cookies (multi-user deployment)
    if cookie_controller:
        try:
            cookie_val = cookie_controller.get("dailysync_profile")
            if cookie_val:
                if isinstance(cookie_val, str):
                    profile = json.loads(cookie_val)
                elif isinstance(cookie_val, dict):
                    profile = cookie_val
        except Exception:
            pass
            
    # 2. Try to load from dailysync_profile.json (fallback for local runs)
    if not profile and os.path.exists(DEFAULT_PROFILE_PATH):
        try:
            with open(DEFAULT_PROFILE_PATH, "r") as f:
                profile = json.load(f)
        except Exception as e:
            st.sidebar.error(f"⚠️ Could not load auto-saved profile: {e}")
            
    # 3. Set defaults in session state (preferring profile if truthy, falling back to .env, falling back to system defaults)
    st.session_state.to_email = profile.get("to_email") or os.getenv("TEAM_LEAD_1") or "sravanik@galactixsolutions.com"
    st.session_state.cc_email = profile.get("cc_email") or os.getenv("TEAM_LEAD_2") or "vipinm@galactixsolutions.com"
    st.session_state.sender_email = profile.get("sender_email") or os.getenv("SENDER_EMAIL") or "lokesh@example.com"
    st.session_state.sender_password = profile.get("sender_password") or os.getenv("SENDER_PASSWORD") or ""
    
    provider_init = profile.get("llm_provider") or os.getenv("LLM_PROVIDER") or "nvidia"
    provider_init = provider_init.lower()
    if provider_init not in ["nvidia", "gemini", "openai", "mock"]:
        provider_init = "nvidia"
    st.session_state.llm_provider = provider_init
    
    # Initialize provider-specific keys (handling backward compatibility with "api_key")
    saved_api_key = profile.get("api_key", "")
    st.session_state.nvidia_api_key = profile.get("nvidia_api_key") or (saved_api_key if provider_init == "nvidia" else "") or os.getenv("NVIDIA_API_KEY") or ""
    st.session_state.gemini_api_key = profile.get("gemini_api_key") or (saved_api_key if provider_init == "gemini" else "") or os.getenv("GEMINI_API_KEY") or ""
    st.session_state.openai_api_key = profile.get("openai_api_key") or (saved_api_key if provider_init == "openai" else "") or os.getenv("OPENAI_API_KEY") or ""
    
    st.session_state.smtp_server = profile.get("smtp_server") or os.getenv("SMTP_SERVER") or "smtp.gmail.com"
    st.session_state.smtp_port = profile.get("smtp_port") or os.getenv("SMTP_PORT") or "587"
    st.session_state.profile_loaded = True

# Settings Profile Import
st.sidebar.markdown("<h3 style='color:#60a5fa; margin-top:0;'>💾 Settings Profile</h3>", unsafe_allow_html=True)
profile_file = st.sidebar.file_uploader(
    "Import profile config (.json):", 
    type=["json"],
    help="Upload your saved dailysync_profile.json file to automatically populate all settings."
)

if profile_file is not None:
    try:
        profile = json.load(profile_file)
        st.session_state.to_email = profile.get("to_email") or os.getenv("TEAM_LEAD_1") or "sravanik@galactixsolutions.com"
        st.session_state.cc_email = profile.get("cc_email") or os.getenv("TEAM_LEAD_2") or "vipinm@galactixsolutions.com"
        st.session_state.sender_email = profile.get("sender_email") or os.getenv("SENDER_EMAIL") or "lokesh@example.com"
        st.session_state.sender_password = profile.get("sender_password") or os.getenv("SENDER_PASSWORD") or ""
        
        provider_upd = profile.get("llm_provider") or os.getenv("LLM_PROVIDER") or "nvidia"
        provider_upd = provider_upd.lower()
        st.session_state.llm_provider = provider_upd
        
        saved_api_key = profile.get("api_key", "")
        st.session_state.nvidia_api_key = profile.get("nvidia_api_key") or (saved_api_key if provider_upd == "nvidia" else "") or os.getenv("NVIDIA_API_KEY") or ""
        st.session_state.gemini_api_key = profile.get("gemini_api_key") or (saved_api_key if provider_upd == "gemini" else "") or os.getenv("GEMINI_API_KEY") or ""
        st.session_state.openai_api_key = profile.get("openai_api_key") or (saved_api_key if provider_upd == "openai" else "") or os.getenv("OPENAI_API_KEY") or ""
        
        st.session_state.smtp_server = profile.get("smtp_server") or os.getenv("SMTP_SERVER") or "smtp.gmail.com"
        st.session_state.smtp_port = profile.get("smtp_port") or os.getenv("SMTP_PORT") or "587"
        st.sidebar.success("✅ Profile loaded!")
    except Exception as e:
        st.sidebar.error(f"❌ Failed to parse profile: {e}")

st.sidebar.markdown("---")

# LLM Config (Allows each user to supply their own key)
st.sidebar.markdown("<h3 style='color:#e2e8f0; font-size:1.1rem;'>🔑 LLM Configuration</h3>", unsafe_allow_html=True)

# Select provider
provider_default = st.session_state.llm_provider
llm_provider = st.sidebar.selectbox(
    "LLM Provider:",
    options=["nvidia", "gemini", "openai", "mock"],
    index=["nvidia", "gemini", "openai", "mock"].index(provider_default),
    help="Select the AI model provider."
)
st.session_state.llm_provider = llm_provider

# API Key input
user_key = ""
if llm_provider != "mock":
    env_key = os.getenv(f"{llm_provider.upper()}_API_KEY", "")
    placeholder_text = "Using default server key" if env_key else "Paste your API Key here"
    
    # Retrieve provider-specific key from session state
    default_key_val = st.session_state.get(f"{llm_provider.lower()}_api_key", "")
    
    user_key = st.sidebar.text_input(
        f"{llm_provider.upper()} API Key:",
        type="password",
        value=default_key_val,
        placeholder=placeholder_text,
        help="Paste your own API key here. Leave empty to use the default server key."
    ).strip()

    # Save to provider-specific key in session state
    st.session_state[f"{llm_provider.lower()}_api_key"] = user_key

st.sidebar.markdown("---")

# Recipients Settings
st.sidebar.markdown("<h3 style='color:#e2e8f0; font-size:1.1rem;'>📧 Recipients (Team Leads)</h3>", unsafe_allow_html=True)
team_lead_1 = st.sidebar.text_input(
    "To: (Primary Recipients)", 
    value=st.session_state.get("to_email", ""),
    help="Separate multiple email addresses with commas."
)
team_lead_2 = st.sidebar.text_input(
    "Cc: (Carbon Copy)", 
    value=st.session_state.get("cc_email", ""),
    help="Separate multiple email addresses with commas."
)

st.session_state.to_email = team_lead_1
st.session_state.cc_email = team_lead_2

st.sidebar.markdown("---")

# SMTP Details
st.sidebar.markdown("<h3 style='color:#e2e8f0; font-size:1.1rem;'>🔑 Sender Credentials</h3>", unsafe_allow_html=True)
smtp_server = st.sidebar.text_input("SMTP Server", value=st.session_state.get("smtp_server", ""))
smtp_port = st.sidebar.text_input("SMTP Port", value=st.session_state.get("smtp_port", ""))
sender_email = st.sidebar.text_input("Sender Email", value=st.session_state.get("sender_email", ""))
sender_pwd = st.sidebar.text_input("Sender Password", value=st.session_state.get("sender_password", ""), type="password")

st.session_state.smtp_server = smtp_server
st.session_state.smtp_port = smtp_port
st.session_state.sender_email = sender_email
st.session_state.sender_password = sender_pwd

# Profile Helper for autosave/saving
def save_profile_settings():
    profile_data = {
        "to_email": team_lead_1,
        "cc_email": team_lead_2,
        "sender_email": sender_email,
        "sender_password": sender_pwd,
        "llm_provider": llm_provider,
        "nvidia_api_key": st.session_state.get("nvidia_api_key", ""),
        "gemini_api_key": st.session_state.get("gemini_api_key", ""),
        "openai_api_key": st.session_state.get("openai_api_key", ""),
        "api_key": user_key,
        "smtp_server": smtp_server,
        "smtp_port": smtp_port
    }
    
    # 1. Save to browser cookies (client-side for multi-user deployment)
    if cookie_controller:
        try:
            cookie_controller.set("dailysync_profile", profile_data)
        except Exception:
            pass
            
    # 2. Save to local file (server-side backup for local runs)
    try:
        with open(DEFAULT_PROFILE_PATH, "w") as f:
            json.dump(profile_data, f, indent=2)
        return True
    except Exception as e:
        return False

# Settings buttons (Save as Default and Export Profile Settings)
col_save, col_export = st.sidebar.columns(2)
with col_save:
    if st.button("💾 Save as Default", help="Save these configurations locally so they load automatically next time."):
        if save_profile_settings():
            st.success("✅ Saved default!")
        else:
            st.error("❌ Save failed.")

with col_export:
    profile_data = {
        "to_email": team_lead_1,
        "cc_email": team_lead_2,
        "sender_email": sender_email,
        "sender_password": sender_pwd,
        "llm_provider": llm_provider,
        "nvidia_api_key": st.session_state.get("nvidia_api_key", ""),
        "gemini_api_key": st.session_state.get("gemini_api_key", ""),
        "openai_api_key": st.session_state.get("openai_api_key", ""),
        "api_key": user_key,
        "smtp_server": smtp_server,
        "smtp_port": smtp_port
    }
    profile_json = json.dumps(profile_data, indent=2)
    st.download_button(
        label="📤 Export Profile",
        data=profile_json,
        file_name="dailysync_profile.json",
        mime="application/json",
        help="Download your current configurations to your computer so you can upload them next time!"
    )

# File uploader and checker status
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#e2e8f0; font-size:1.1rem;'>📊 Excel Database</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload your Excel tracker:", type=["xlsx"])

excel_file = None
if uploaded_file is not None:
    # Save the uploaded file to a temporary location inside the workspace
    temp_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    excel_file = os.path.join(temp_dir, f"uploaded_{uploaded_file.name}")
    with open(excel_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"📂 Active Sheet:\n`{uploaded_file.name}` (Uploaded)")
else:
    # Fallback to local files if no upload
    excel_file = find_excel_file()
    if excel_file:
        st.sidebar.warning(f"📂 Active Sheet:\n`{os.path.basename(excel_file)}` (Local File)")
    else:
        st.sidebar.error("❌ No Excel sheet uploaded or found locally!")

# Provide a template Excel download option for new users
template_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "Daily_Tasks.xlsx")
if os.path.exists(template_path):
    with open(template_path, "rb") as tf:
        st.sidebar.download_button(
            label="📥 Download Excel Template",
            data=tf,
            file_name="Daily_Tasks_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download the blank template Excel sheet to start tracking your daily tasks."
        )

# Main Title Section
st.markdown("<div class='title-gradient'>DailySync</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>AI-Powered Internship Daily Reporting Agent</div>", unsafe_allow_html=True)

# Grid Layout for App
col1, col2 = st.columns([1.1, 0.9])

with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📝 Today's Tasks")
    st.write("Enter your raw, informal tasks below. The AI Agent will parse, professionalize, and catalog them.")
    
    default_tasks = """Today I will:
* Build authentication module
* Fix API integration issues
* Test RAG pipeline
* Review deployment workflow"""
    
    raw_input = st.text_area(
        "Raw Tasks",
        value=default_tasks,
        height=200,
        placeholder="Type tasks here...",
        label_visibility="collapsed"
    )
    
    preview_mode = st.checkbox(
        "Preview Report & Email before sending", 
        value=True,
        help="If checked, you can verify the parsed tasks, Excel spreadsheet, and email body draft before sending them to your team leads."
    )
    
    # Trigger Action
    btn_text = "Generate Report & Preview" if preview_mode else "Generate & Send Report"
    if st.button(btn_text):
        if not raw_input.strip():
            st.error("Please enter some tasks before submitting.")
        elif not excel_file:
            st.error("No Excel workbook found. Please place a .xlsx tracker file in the project directory.")
        else:
            # Autosave current settings as default profile
            save_profile_settings()
            
            st.session_state.processing = True
            st.session_state.agent_result = None
            
            with st.spinner("Processing tasks and preparing report..."):
                try:
                    # Initialize LangGraph Agent
                    graph = create_agent_graph()
                    
                    # Run the agent
                    initial_state = {
                        "raw_tasks_input": raw_input,
                        "preview_mode": preview_mode,
                        "tasks": [],
                        "excel_path": excel_file,
                        "excel_headers": [],
                        "excel_updated": False,
                        "email_subject": "",
                        "email_body": "",
                        "email_sent": False,
                        "status_log": [],
                        "error": "",
                        
                        # Thread-safe credentials passed directly inside State
                        "llm_provider": llm_provider,
                        "llm_api_key": st.session_state.get(f"{llm_provider.lower()}_api_key", ""),
                        "smtp_server": smtp_server,
                        "smtp_port": smtp_port,
                        "sender_email": sender_email,
                        "sender_password": sender_pwd,
                        "to_email": team_lead_1,
                        "cc_email": team_lead_2
                    }
                    
                    result = graph.invoke(initial_state)
                    st.session_state.agent_result = result
                    
                except Exception as ex:
                    st.error(f"Execution Error: {str(ex)}")
                finally:
                    st.session_state.processing = False
                    
    st.markdown('</div>', unsafe_allow_html=True)

    # Display Logging and Status updates
    if st.session_state.agent_result:
        res = st.session_state.agent_result
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("⚙️ Agent Execution Log")
        
        log_text = "\n".join([f"• {log}" for log in res.get("status_log", [])])
        st.markdown(f"<div class='log-card'>{log_text}</div>", unsafe_allow_html=True)
        
        if res.get("error"):
            st.error(f"⚠️ Agent stopped with an error:\n{res.get('error')}")
        elif res.get("email_sent"):
            st.success("🎉 Process Complete! Excel updated and Email successfully dispatched to team leads.")
        else:
            st.info("ℹ️ Tasks processed and Excel updated. Email generated and waiting for approval below.")
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    if st.session_state.agent_result:
        res = st.session_state.agent_result
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔍 Previews & Results")
        
        # Tabs for result previews
        tab1, tab2, tab3 = st.tabs(["📋 Structured Tasks", "📊 Excel Sheets", "✉️ Email Draft"])
        
        with tab1:
            tasks_data = res.get("tasks", [])
            if tasks_data:
                df = pd.DataFrame(tasks_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.write("No tasks structured.")
                
        with tab2:
            excel_path = res.get("excel_path")
            if excel_path and os.path.exists(excel_path):
                # Read dynamic worksheets or main sheet
                df_excel = pd.read_excel(excel_path)
                st.write(f"Updated Workbook: `{os.path.basename(excel_path).replace('uploaded_', '')}`")
                
                # Render download button
                with open(excel_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Updated Excel Tracker",
                        data=file,
                        file_name=os.path.basename(excel_path).replace("uploaded_", ""),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                st.dataframe(df_excel.tail(10), use_container_width=True) # Show last 10 rows
            else:
                st.write("No Excel changes made.")
                
        with tab3:
            subject = res.get("email_subject")
            body = res.get("email_body")
            if subject and body:
                st.markdown("⚠️ *You can edit the Subject and Content below before confirming the email send:*")
                edited_subject = st.text_input("Subject:", value=subject)
                edited_body = st.text_area("Email Content:", value=body, height=250)
                
                # Keep session state updated with edits
                st.session_state.agent_result["email_subject"] = edited_subject
                st.session_state.agent_result["email_body"] = edited_body
            else:
                st.write("No email draft generated.")
                
        # Send Email action (if paused in Preview mode)
        if not res.get("email_sent") and not res.get("error") and res.get("email_body"):
            st.markdown("---")
            st.markdown("<div class='send-btn'>", unsafe_allow_html=True)
            if st.button("🚀 Confirm & Dispatch Email"):
                with st.spinner("Dispatching email..."):
                    updated_state = email_sender_node(res)
                    # Update local state
                    st.session_state.agent_result.update(updated_state)
                    if updated_state.get("error"):
                        st.error(f"Failed to send email: {updated_state.get('error')}")
                    else:
                        st.success("🎉 Success! Excel sheet tracker sent to team leads.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="glass-card" style="text-align: center; color: #64748b; padding: 60px 20px;">', unsafe_allow_html=True)
        st.markdown("<h3>📊 Previews will appear here after report generation.</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Task History section
if excel_file and os.path.exists(excel_file):
    try:
        df_hist = pd.read_excel(excel_file)
        if not df_hist.empty:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📚 Task History Log")
            st.write("Recent history extracted from your Excel workbook database:")
            st.dataframe(df_hist.tail(15), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.sidebar.warning(f"Could not load history: {e}")
