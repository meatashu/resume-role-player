import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import bcrypt
from pathlib import Path
import sys
import os

# Add parent directory to path to import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.llm import OllamaLLM
from src.persona import PersonaManager
from src.knowledge_base import KnowledgeBase

# Initialize session state
def init_session_state():
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None

def load_admin_password():
    """Return hardcoded password"""
    return "admin123"

def verify_password(password, stored_password):
    """Simple string comparison for password verification"""
    return password == "admin123"  # Hardcoded password check

def save_interaction(persona, query, response):
    """Save interaction to log file"""
    interaction = {
        'timestamp': datetime.now().isoformat(),
        'persona': persona,
        'query': query,
        'response': response
    }
    
    log_file = Path('data/interactions.json')
    log_file.parent.mkdir(exist_ok=True)
    
    interactions = []
    if log_file.exists():
        with open(log_file) as f:
            interactions = json.load(f)
    
    interactions.append(interaction)
    
    with open(log_file, 'w') as f:
        json.dump(interactions, f, indent=2)

def load_restricted_queries():
    """Load list of restricted queries"""
    restricted_file = Path('data/restricted.json')
    if restricted_file.exists():
        with open(restricted_file) as f:
            return json.load(f)
    return {'queries': [], 'topics': []}

def is_query_restricted(query):
    """Check if query is restricted"""
    restricted = load_restricted_queries()
    query = query.lower()
    
    # Check exact matches
    if any(q.lower() in query for q in restricted['queries']):
        return True
        
    # Check topic matches
    if any(topic.lower() in query for topic in restricted['topics']):
        return True
    
    return False

def main():
    st.set_page_config(page_title="AshuBot - The Multipotentialite", layout="wide")
    init_session_state()
    
    # Initialize bot components
    if 'persona_manager' not in st.session_state:
        llm = OllamaLLM()
        knowledge = KnowledgeBase()
        st.session_state.persona_manager = PersonaManager(llm, knowledge)
    
    # Sidebar for mode selection and authentication
    with st.sidebar:
        st.title("🤖 AshuBot")
        mode = st.radio("Select Mode", ["Interviewer", "Admin"])
        
        if mode == "Admin" and st.session_state.auth_status != "authenticated":
            with st.form("admin_auth"):
                password = st.text_input("Admin Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    st.write("Debug - Login attempt")
                    st.write(f"Debug - Password entered: {'Yes' if password else 'No'}")
                    stored_hash = load_admin_password()
                    st.write(f"Debug - Stored hash loaded: {'Yes' if stored_hash else 'No'}")
                    if stored_hash and verify_password(password, stored_hash):
                        st.write("Debug - Password verified successfully")
                        st.session_state.auth_status = "authenticated"
                        st.session_state.current_mode = "Admin"
                        st.rerun()
                    else:
                        st.write("Debug - Password verification failed")
                        st.error("Invalid password")
        
        if mode == "Interviewer" or st.session_state.auth_status == "authenticated":
            st.session_state.current_mode = mode
            
            # Persona selection
            st.subheader("Choose a Persona")
            persona = st.selectbox(
                "Role",
                st.session_state.persona_manager.get_available_roles(),
                key="persona_selector"
            )
            
            # Update current persona and switch if changed
            if st.session_state.current_persona != persona:
                st.session_state.current_persona = persona
                st.session_state.persona_manager.switch_persona(persona)
                # Clear chat history when switching personas
                if 'chat_history' in st.session_state:
                    st.session_state.chat_history = []
    
    # Main content area
    if st.session_state.current_mode == "Admin":
        # Admin Dashboard
        st.title("Admin Dashboard")
        
        # Ollama Server Status Section
        with st.sidebar:
            st.divider()
            st.subheader("🚀 Ollama Server Status")
            server_status = st.session_state.persona_manager.llm.get_server_status()
            
            # Server Status Indicator
            status_color = "🟢" if server_status["status"] == "online" else "🔴"
            st.write(f"{status_color} Server Status: {server_status['status']}")
            st.write(f"📡 Host: {server_status['host']}")
            
            if server_status["status"] != "online":
                st.error("Ollama server is not running!")
                with st.expander("📋 Setup Instructions"):
                    st.markdown("""
                    1. **Install Ollama** (if not installed):
                       - Visit [ollama.ai](https://ollama.ai)
                       - Download and install for your system
                    
                    2. **Start Ollama Server**:
                       ```bash
                       ollama serve
                       ```
                    
                    3. **Pull Required Model**:
                       ```bash
                       ollama pull mistral
                       ```
                    
                    4. **Verify Status**:
                       - Click "Update Server" to refresh status
                    """)
            
            # Server Configuration
            with st.expander("Configure Server"):
                new_host = st.text_input("Ollama Server URL", 
                                       value=server_status['host'],
                                       placeholder="http://localhost:11434")
                if st.button("Update Server"):
                    updated_status = st.session_state.persona_manager.llm.update_host(new_host)
                    if updated_status["status"] == "online":
                        st.success("Server updated successfully!")
                    else:
                        st.error(f"Failed to connect: {updated_status.get('error', 'Unknown error')}")
            
            # Available Models
            if server_status["status"] == "online":
                st.write("📚 Available Models:")
                for model in server_status.get("models", []):
                    st.code(f"{model['name']} ({model['digest'][:8]})")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Analytics", "Knowledge Base", "Content Moderation", "Feedback", "Ollama Monitor"
        ])
        
        # Add Ollama Monitor tab
        with tab5:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("🔄 Ollama Live Monitor")
                
                # Ollama Demo Section
                st.write("### 🎮 Quick Test")
                with st.form("ollama_test"):
                    test_model = st.selectbox(
                        "Select Model",
                        options=[m["name"] for m in server_status.get("models", [])] or ["mistral"],
                        key="test_model"
                    )
                    if st.form_submit_button("Run Test Generation"):
                        with st.spinner("Generating response..."):
                            result = st.session_state.persona_manager.llm.test_generation(test_model)
                            if result["success"]:
                                st.success("Test successful!")
                                st.write("**Prompt:**", result["prompt"])
                                st.write("**Response:**", result["response"])
                            else:
                                st.error(f"Test failed: {result['error']}")
                                st.info(f"Details: {result['details']}")
                
                # Ollama Logs Section
                st.write("### 📜 Server Logs")
                if server_status["status"] == "online":
                    try:
                        # Get Ollama logs using journalctl
                        with st.spinner("Fetching logs..."):
                            result = os.popen("journalctl -u ollama -n 50 2>/dev/null || log stream --predicate 'processImagePath contains \"ollama\"' --style compact --no-info --last 2m 2>/dev/null || echo 'No logs available'").read()
                            st.code(result, language="bash")
                            
                            if st.button("🔄 Refresh Logs"):
                                st.rerun()
                    except Exception as e:
                        st.error(f"Could not fetch logs: {str(e)}")
                else:
                    st.warning("Server is offline - logs not available")
            
            with col2:
                st.subheader("📊 Server Metrics")
                if server_status["status"] == "online":
                    try:
                        # Get server metrics if available
                        metrics = {
                            "Active Models": len(server_status.get("models", [])),
                            "Server URL": server_status["host"],
                            "Status": "Running 🟢"
                        }
                        
                        for key, value in metrics.items():
                            st.metric(key, value)
                    except Exception as e:
                        st.error(f"Error fetching metrics: {str(e)}")
        
        with tab1:
            st.header("Interaction Analytics")
            
            # Load interaction data
            log_file = Path('data/interactions.json')
            if log_file.exists():
                with open(log_file) as f:
                    interactions = json.load(f)
                    
                df = pd.DataFrame(interactions)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Daily interaction count
                daily_counts = df.groupby(df['timestamp'].dt.date).size().reset_index()
                daily_counts.columns = ['date', 'count']
                
                st.subheader("Daily Interactions")
                fig = px.line(daily_counts, x='date', y='count')
                st.plotly_chart(fig)
                
                # Persona usage
                st.subheader("Persona Usage")
                persona_counts = df['persona'].value_counts()
                fig = px.pie(values=persona_counts.values, names=persona_counts.index)
                st.plotly_chart(fig)
                
                # Recent interactions
                st.subheader("Recent Interactions")
                st.dataframe(df.tail(10)[['timestamp', 'persona', 'query', 'response']])
        
        with tab2:
            st.header("Knowledge Base Management")
            
            # Tabs for direct edit vs staged changes
            kb_tab1, kb_tab2 = st.tabs(["Direct Edit", "Review Staged Changes"])
            
            with kb_tab1:
                # Knowledge base editor
                kb_file = st.selectbox(
                    "Select file to edit",
                    ["cv.json", "projects.json", "patents.json"]
                )
                
                kb_path = Path(f'knowledge_base/{kb_file}')
                if kb_path.exists():
                    with open(kb_path) as f:
                        content = json.load(f)
                    
                    edited_content = st.json_editor(content)
                    
                    if st.button("Save Changes"):
                        with open(kb_path, 'w') as f:
                            json.dump(edited_content, f, indent=2)
                        st.success("Changes saved successfully!")
            
            with kb_tab2:
                from src.staging import list_staged_entries, preview_merge_changes
                from src.staging import approve_staged_entry, reject_staged_entry
                
                # List staged entries
                st.subheader("Staged Changes")
                staged = list_staged_entries()
                
                if not staged:
                    st.info("No staged changes waiting for review.")
                else:
                    for entry in staged:
                        with st.expander(f"📝 {entry['id']} - {entry['timestamp']}"):
                            st.write("**Status:** ", entry['status'])
                            st.write("**Source:** ")
                            st.json(entry['source'])
                            
                            if entry['status'] == 'pending':
                                # Show preview
                                st.write("**Preview Changes:** ")
                                preview = preview_merge_changes(entry['id'])
                                st.json(preview)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Approve", key=f"approve_{entry['id']}"):
                                        result = approve_staged_entry(entry['id'])
                                        st.success("Changes approved and merged!")
                                        st.json(result)
                                        st.rerun()
                                
                                with col2:
                                    if st.button("❌ Reject", key=f"reject_{entry['id']}"):
                                        reason = st.text_input("Rejection reason:", key=f"reason_{entry['id']}")
                                        if reason:
                                            result = reject_staged_entry(entry['id'], reason)
                                            st.error("Changes rejected.")
                                            st.json(result)
                                            st.rerun()
        
        with tab3:
            st.header("Content Moderation")
            
            restricted = load_restricted_queries()
            
            # Add new restrictions
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Restricted Queries")
                new_query = st.text_input("Add restricted query")
                if st.button("Add Query"):
                    restricted['queries'].append(new_query)
                    with open('data/restricted.json', 'w') as f:
                        json.dump(restricted, f, indent=2)
                    st.success("Query added to restrictions!")
                
                st.write("Current restricted queries:")
                for query in restricted['queries']:
                    st.text(f"• {query}")
            
            with col2:
                st.subheader("Restricted Topics")
                new_topic = st.text_input("Add restricted topic")
                if st.button("Add Topic"):
                    restricted['topics'].append(new_topic)
                    with open('data/restricted.json', 'w') as f:
                        json.dump(restricted, f, indent=2)
                    st.success("Topic added to restrictions!")
                
                st.write("Current restricted topics:")
                for topic in restricted['topics']:
                    st.text(f"• {topic}")
        
        with tab4:
            st.header("User Feedback")
            
            # Display feedback if available
            feedback_file = Path('data/feedback.json')
            if feedback_file.exists():
                with open(feedback_file) as f:
                    feedback = json.load(f)
                
                for item in feedback:
                    with st.expander(f"Feedback from {item['timestamp']}"):
                        st.write(f"Rating: {'⭐' * item['rating']}")
                        st.write(f"Comment: {item['comment']}")
                        st.write(f"Persona: {item['persona']}")
    
    else:
        # Interviewer Mode
        st.title(f"Chat with AshuBot - {st.session_state.current_persona}")
        
        # Chat interface
        chat_placeholder = st.chat_input("Ask me anything...")
        if chat_placeholder:
            if is_query_restricted(chat_placeholder):
                st.error("I apologize, but I cannot answer questions on this topic.")
            else:
                response = st.session_state.persona_manager.get_response(chat_placeholder)
                save_interaction(st.session_state.current_persona, chat_placeholder, response)
                st.session_state.chat_history.append({"role": "user", "content": chat_placeholder})
                st.session_state.chat_history.append({"role": "assistant", "content": response})        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Feedback form
        with st.expander("Provide Feedback"):
            with st.form("feedback_form"):
                rating = st.slider("Rate your experience", 1, 5, 5)
                comment = st.text_area("Additional comments")
                submit_feedback = st.form_submit_button("Submit Feedback")
                
                if submit_feedback:
                    feedback = {
                        'timestamp': datetime.now().isoformat(),
                        'rating': rating,
                        'comment': comment,
                        'persona': st.session_state.current_persona
                    }
                    
                    feedback_file = Path('data/feedback.json')
                    feedback_list = []
                    
                    if feedback_file.exists():
                        with open(feedback_file) as f:
                            feedback_list = json.load(f)
                    
                    feedback_list.append(feedback)
                    
                    feedback_file.parent.mkdir(exist_ok=True)
                    with open(feedback_file, 'w') as f:
                        json.dump(feedback_list, f, indent=2)
                    
                    st.success("Thank you for your feedback!")

if __name__ == "__main__":
    main()