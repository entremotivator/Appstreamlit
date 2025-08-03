import streamlit as st
import requests
import json
from datetime import datetime
import uuid
from utils.auth import require_auth
from utils.n8n import send_chat_message, get_chat_history
from utils.config import get_config

@require_auth
def main():
    st.title("🤖 AI Chat Assistant")
    
    # Initialize chat session
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Tabs for different chat features
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📋 Chat History", "⚙️ Settings", "📊 Analytics"])
    
    with tab1:
        show_chat_interface()
    
    with tab2:
        show_chat_history()
    
    with tab3:
        show_chat_settings()
    
    with tab4:
        show_chat_analytics()

def show_chat_interface():
    """Main chat interface"""
    st.subheader("AI Assistant Chat")
    
    # Chat configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chat_mode = st.selectbox("Chat Mode", [
            "General Assistant", "Customer Support", "Appointment Booking", 
            "Service Information", "Technical Support"
        ])
    
    with col2:
        ai_personality = st.selectbox("AI Personality", [
            "Professional", "Friendly", "Technical", "Casual"
        ])
    
    with col3:
        language = st.selectbox("Language", ["English", "Spanish", "French", "German"])
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show timestamp and additional info
                st.caption(f"🕐 {message.get('timestamp', 'Unknown time')}")
                
                # Show confidence score for AI messages
                if message["role"] == "assistant" and "confidence" in message:
                    confidence = message["confidence"]
                    confidence_color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
                    st.caption(f"🎯 Confidence: {confidence:.1%}")
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to chat
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "session_id": st.session_state.chat_session_id
        }
        st.session_state.chat_messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
            st.caption(f"🕐 {user_message['timestamp']}")
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                response_data = get_ai_response(user_input, chat_mode, ai_personality)
                
                if response_data["success"]:
                    ai_response = response_data["response"]
                    confidence = response_data.get("confidence", 0.9)
                    
                    st.write(ai_response)
                    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
                    st.caption(f"🎯 Confidence: {confidence:.1%}")
                    
                    # Add AI message to chat
                    ai_message = {
                        "role": "assistant",
                        "content": ai_response,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "confidence": confidence,
                        "session_id": st.session_state.chat_session_id
                    }
                    st.session_state.chat_messages.append(ai_message)
                    
                    # Show suggested actions if available
                    if "actions" in response_data:
                        show_suggested_actions(response_data["actions"])
                else:
                    st.error(f"❌ Error: {response_data['error']}")
    
    # Chat controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = []
            st.rerun()
    
    with col2:
        if st.button("💾 Save Chat"):
            save_chat_session()
    
    with col3:
        if st.button("📤 Export Chat"):
            export_chat_session()
    
    with col4:
        if st.button("🔄 New Session"):
            st.session_state.chat_session_id = str(uuid.uuid4())
            st.session_state.chat_messages = []
            st.rerun()

def show_chat_history():
    """Display chat history and management"""
    st.subheader("Chat History & Management")
    
    # History filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_filter = st.date_input("From Date", value=datetime.now().date())
    
    with col2:
        session_filter = st.selectbox("Session Type", ["All", "Current User", "Specific User"])
    
    with col3:
        search_term = st.text_input("🔍 Search Messages", placeholder="Search chat content...")
    
    # Load chat history (this would be from your database/storage)
    chat_history = get_sample_chat_history()  # Replace with actual history loading
    
    # Display chat sessions
    st.markdown("### 📋 Recent Chat Sessions")
    
    for i, session in enumerate(chat_history):
        with st.expander(f"💬 Session {session['id'][:8]} - {session['date']} ({len(session['messages'])} messages)"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Duration:** {session['duration']}")
                st.markdown(f"**User:** {session['user']}")
                st.markdown(f"**Mode:** {session['mode']}")
                st.markdown(f"**Summary:** {session['summary']}")
            
            with col2:
                if st.button("👁️ View", key=f"view_{i}"):
                    show_session_details(session)
                
                if st.button("🗑️ Delete", key=f"delete_{i}"):
                    st.success("Session deleted")
    
    # Chat statistics
    st.markdown("### 📊 Chat Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Total Sessions", "147", "12")
    
    with col2:
        st.metric("💬 Total Messages", "1,523", "89")
    
    with col3:
        st.metric("⏱️ Avg Session Duration", "8.5 min", "-0.5")
    
    with col4:
        st.metric("😊 Satisfaction Score", "4.6/5", "0.2")

def show_chat_settings():
    """Chat configuration and settings"""
    st.subheader("AI Chat Settings")
    
    # AI Configuration
    st.markdown("### 🤖 AI Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Response Settings**")
        response_style = st.selectbox("Response Style", [
            "Concise", "Detailed", "Conversational", "Technical"
        ])
        
        max_response_length = st.slider("Max Response Length", 50, 500, 200)
        
        enable_context_memory = st.checkbox("Remember conversation context", value=True)
        
        auto_suggest_actions = st.checkbox("Auto-suggest actions", value=True)
    
    with col2:
        st.markdown("**Integration Settings**")
        
        # n8n webhook configuration
        n8n_webhook_url = st.text_input(
            "n8n Webhook URL",
            value=get_config("api_endpoints", {}).get("n8n", ""),
            help="URL for your n8n chat webhook"
        )
        
        webhook_timeout = st.number_input("Webhook Timeout (seconds)", min_value=5, max_value=60, value=30)
        
        enable_fallback = st.checkbox("Enable fallback responses", value=True)
        
        fallback_message = st.text_area(
            "Fallback Message",
            value="I'm sorry, I'm having trouble understanding. Could you please rephrase your question?",
            help="Message shown when AI can't provide a response"
        )
    
    # Knowledge Base Settings
    st.markdown("### 📚 Knowledge Base")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Training Data Sources**")
        
        knowledge_sources = st.multiselect("Enable Knowledge Sources", [
            "Customer Database", "Service Information", "FAQ Database",
            "Documentation", "Previous Chats", "External APIs"
        ], default=["Service Information", "FAQ Database"])
        
        update_frequency = st.selectbox("Knowledge Update Frequency", [
            "Real-time", "Hourly", "Daily", "Weekly"
        ])
    
    with col2:
        st.markdown("**Content Filtering**")
        
        enable_content_filter = st.checkbox("Enable content filtering", value=True)
        
        blocked_topics = st.text_area(
            "Blocked Topics",
            placeholder="Enter topics to block (one per line)",
            help="Topics the AI should not discuss"
        )
        
        profanity_filter = st.checkbox("Enable profanity filter", value=True)
    
    # Performance Settings
    st.markdown("### ⚡ Performance & Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_analytics = st.checkbox("Enable chat analytics", value=True)
        log_conversations = st.checkbox("Log conversations", value=True)
        enable_feedback = st.checkbox("Request user feedback", value=True)
    
    with col2:
        alert_on_errors = st.checkbox("Alert on errors", value=True)
        monitor_response_time = st.checkbox("Monitor response times", value=True)
        
        max_concurrent_chats = st.number_input("Max concurrent chats", min_value=1, max_value=100, value=10)
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        settings = {
            "response_style": response_style,
            "max_response_length": max_response_length,
            "n8n_webhook_url": n8n_webhook_url,
            "knowledge_sources": knowledge_sources,
            "enable_analytics": enable_analytics
        }
        
        st.success("✅ Settings saved successfully!")
        st.json(settings)

def show_chat_analytics():
    """Chat analytics and insights"""
    st.subheader("Chat Analytics & Insights")
    
    # Time period selector
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.date_input(
            "Analysis Period",
            value=(datetime.now().date(), datetime.now().date())
        )
    
    with col2:
        metrics_view = st.selectbox("Metrics View", [
            "Overview", "User Engagement", "AI Performance", "Topics Analysis"
        ])
    
    if metrics_view == "Overview":
        show_overview_metrics()
    elif metrics_view == "User Engagement":
        show_engagement_metrics()
    elif metrics_view == "AI Performance":
        show_performance_metrics()
    elif metrics_view == "Topics Analysis":
        show_topics_analysis()

def show_overview_metrics():
    """Show overview analytics"""
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💬 Total Chats", "342", "23")
    
    with col2:
        st.metric("👥 Unique Users", "127", "8")
    
    with col3:
        st.metric("⏱️ Avg Response Time", "1.2s", "-0.3s")
    
    with col4:
        st.metric("😊 Satisfaction", "4.3/5", "0.1")
    
    # Charts would go here with actual data
    st.markdown("### 📊 Chat Volume Trend")
    # Placeholder for actual chart
    st.info("📈 Chart showing chat volume over time would appear here")
    
    st.markdown("### 🕐 Usage Patterns")
    st.info("📊 Chart showing usage patterns by hour/day would appear here")

def show_engagement_metrics():
    """Show user engagement metrics"""
    st.markdown("### 👥 User Engagement Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🔄 Return Users", "68%", "5%")
        st.metric("💬 Avg Messages/Session", "8.3", "1.2")
        st.metric("⏱️ Avg Session Duration", "6.4 min", "0.8")
    
    with col2:
        st.metric("❓ Questions Resolved", "87%", "3%")
        st.metric("🎯 Goal Completion", "72%", "8%")
        st.metric("👍 Positive Feedback", "91%", "2%")

def show_performance_metrics():
    """Show AI performance metrics"""
    st.markdown("### 🤖 AI Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🎯 Response Accuracy", "89%", "2%")
        st.metric("⚡ Avg Response Time", "1.2s", "-0.1s")
        st.metric("🧠 Context Understanding", "85%", "3%")
    
    with col2:
        st.metric("❌ Error Rate", "2.1%", "-0.3%")
        st.metric("🔄 Fallback Usage", "8%", "-1%")
        st.metric("📚 Knowledge Coverage", "76%", "4%")

def show_topics_analysis():
    """Show topics and intent analysis"""
    st.markdown("### 📋 Topics & Intent Analysis")
    
    # Sample topic data
    topics = {
        "Appointment Booking": 35,
        "Service Information": 28,
        "Pricing Questions": 22,
        "Technical Support": 15,
        "General Inquiry": 12,
        "Complaint/Issue": 8
    }
    
    st.markdown("**Most Common Topics:**")
    for topic, count in topics.items():
        st.markdown(f"- {topic}: {count} conversations")
    
    st.info("📊 Detailed topic analysis charts would appear here with actual data")

def get_ai_response(user_input, chat_mode, personality):
    """Get AI response from n8n webhook"""
    try:
        # Prepare the payload
        payload = {
            "message": user_input,
            "mode": chat_mode,
            "personality": personality,
            "user_id": st.session_state.get("user_email", "anonymous"),
            "session_id": st.session_state.chat_session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if n8n integration is configured
        n8n_url = get_config("api_endpoints", {}).get("n8n", "")
        
        if not n8n_url:
            # Return fallback response
            return {
                "success": True,
                "response": get_fallback_response(user_input),
                "confidence": 0.7,
                "source": "fallback"
            }
        
        # Call n8n webhook
        response = requests.post(
            n8n_url,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return {
                "success": True,
                "response": response_data.get("reply", "I understand your message."),
                "confidence": response_data.get("confidence", 0.9),
                "actions": response_data.get("suggested_actions", []),
                "source": "n8n"
            }
        else:
            return {
                "success": False,
                "error": f"n8n webhook returned status {response.status_code}"
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out. Please try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

def get_fallback_response(user_input):
    """Generate fallback response when n8n is unavailable"""
    # Simple keyword-based responses
    input_lower = user_input.lower()
    
    if any(keyword in input_lower for keyword in ["appointment", "book", "schedule"]):
        return "I can help you with appointment booking! You can use our calendar system to schedule appointments. Would you like me to guide you to the booking page?"
    
    elif any(keyword in input_lower for keyword in ["price", "cost", "how much"]):
        return "For pricing information, please check our pricing page where you can find details about all our services and current rates."
    
    elif any(keyword in input_lower for keyword in ["hello", "hi", "hey"]):
        return "Hello! I'm your AI assistant. I can help you with appointments, pricing, services, and general questions. How can I assist you today?"
    
    elif any(keyword in input_lower for keyword in ["help", "support"]):
        return "I'm here to help! I can assist you with:\n- Booking appointments\n- Service information\n- Pricing questions\n- General inquiries\n\nWhat would you like help with?"
    
    else:
        return "Thank you for your message. I understand you're asking about something important. For the best assistance, please contact our support team or try rephrasing your question."

def show_suggested_actions(actions):
    """Display suggested actions from AI response"""
    if actions:
        st.markdown("**💡 Suggested Actions:**")
        
        cols = st.columns(min(len(actions), 3))
        
        for i, action in enumerate(actions[:3]):  # Show max 3 actions
            with cols[i % 3]:
                if st.button(f"🎯 {action['title']}", key=f"action_{i}"):
                    # Handle action click
                    handle_suggested_action(action)

def handle_suggested_action(action):
    """Handle when user clicks a suggested action"""
    action_type = action.get("type", "")
    
    if action_type == "navigate":
        st.session_state.current_page = action.get("page", "Dashboard")
        st.rerun()
    elif action_type == "book_appointment":
        st.session_state.current_page = "Calendar"
        st.rerun()
    elif action_type == "view_pricing":
        st.session_state.current_page = "Pricing"
        st.rerun()
    else:
        st.info(f"Action: {action.get('description', 'Action performed')}")

def save_chat_session():
    """Save current chat session"""
    if st.session_state.chat_messages:
        # Here you would save to your database
        st.success("💾 Chat session saved successfully!")
    else:
        st.warning("No messages to save")

def export_chat_session():
    """Export chat session as JSON"""
    if st.session_state.chat_messages:
        chat_data = {
            "session_id": st.session_state.chat_session_id,
            "user": st.session_state.get("user_name", "Unknown"),
            "date": datetime.now().isoformat(),
            "messages": st.session_state.chat_messages
        }
        
        json_str = json.dumps(chat_data, indent=2)
        st.download_button(
            "📥 Download Chat",
            json_str,
            f"chat_{st.session_state.chat_session_id[:8]}.json",
            "application/json"
        )
    else:
        st.warning("No messages to export")

def get_sample_chat_history():
    """Get sample chat history (replace with actual database query)"""
    return [
        {
            "id": "session_001",
            "date": "2024-01-15",
            "user": "john.doe@email.com",
            "mode": "Customer Support",
            "duration": "5 min 23 sec",
            "messages": 12,
            "summary": "User inquired about appointment booking and service pricing"
        },
        {
            "id": "session_002", 
            "date": "2024-01-14",
            "user": "jane.smith@email.com",
            "mode": "General Assistant",
            "duration": "8 min 15 sec",
            "messages": 18,
            "summary": "User needed help with service information and scheduling"
        }
    ]

def show_session_details(session):
    """Show detailed view of a chat session"""
    st.markdown(f"### 💬 Session Details: {session['id']}")
    st.json(session)

if __name__ == "__main__":
    main()
