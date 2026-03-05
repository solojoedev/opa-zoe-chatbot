import streamlit as st
import anthropic
from function import search_shows
import os

# Page config
st.set_page_config(
    page_title="Zoe - OPA Concierge",
    page_icon="🎭",
    layout="centered"
)

# Password protection
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🎭 Zoe - OPA Concierge")
    st.markdown("*Enter password to access the chatbot*")
    password = st.text_input("Password:", type="password")
    if st.button("Login"):
        if password == "opa2025":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password!")
    st.stop()

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #7B3FF2 0%, #9B59B6 100%);
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🎭 Zoe")
st.caption("Your personal guide to Omaha Performing Arts")

# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greeted = False

# Auto greeting
if not st.session_state.greeted:
    greeting = "Hi! I'm Zoe, your personal guide to Omaha Performing Arts! 🎭\n\nI can help you find shows by month, genre, or venue. What are you looking for today?"
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.session_state.greeted = True

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about shows..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Zoe is thinking..."):
            try:
                # Get API key from Streamlit secrets
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                
                # Tools definition
                tools = [{
                    "name": "search_shows",
                    "description": "Searches for shows at Omaha Performing Arts by month, genre, or venue",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string", "description": "Month (FEB, MAR, APR, MAY, JUN)"},
                            "genre": {"type": "string", "description": "Genre (Broadway, Comedy, Rock, etc.)"},
                            "venue": {"type": "string", "description": "Venue (Orpheum Theater, Holland Center, Steelhouse)"}
                        },
                        "required": []
                    }
                }]
                
                # First API call
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    tools=tools,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Check for tool use
                if message.stop_reason == "tool_use":
                    tool_use = next(block for block in message.content if block.type == "tool_use")
                    
                    # Execute search
                    month = tool_use.input.get("month")
                    genre = tool_use.input.get("genre")
                    venue = tool_use.input.get("venue")
                    results = search_shows(month=month, genre=genre, venue=venue)
                    
                    # Second API call with results
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        tools=tools,
                        messages=[
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": message.content},
                            {
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": tool_use.id,
                                    "content": str(results)
                                }]
                            }
                        ]
                    )
                    answer = response.content[0].text
                else:
                    answer = message.content[0].text
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})