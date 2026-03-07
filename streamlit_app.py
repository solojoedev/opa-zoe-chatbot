import streamlit as st
import anthropic
from function import search_shows

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

# Custom CSS to make it look purple/modern
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background: linear-gradient(180deg, #7B3FF2 0%, #9B59B6 100%);
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: rgba(255,255,255,0.95) !important;
        border-radius: 18px !important;
        margin: 10px 0 !important;
    }
    
    /* User messages - purple */
    [data-testid="stChatMessageContent"][data-testid*="user"] {
        background: linear-gradient(135deg, #7B3FF2 0%, #9B59B6 100%) !important;
        color: white !important;
        border-radius: 18px !important;
        padding: 12px 16px !important;
    }
    
    /* Assistant messages - light gray */
    [data-testid="stChatMessageContent"]:not([data-testid*="user"]) {
        background: #f0f0f0 !important;
        color: #333 !important;
        border-radius: 18px !important;
        padding: 12px 16px !important;
    }
    
    /* Input box */
    .stChatInputContainer {
        background: white !important;
        border-radius: 25px !important;
        padding: 10px !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Title with emoji
st.title("🎭 Zoe")
st.caption("Your personal guide to Omaha Performing Arts")

# Initialize chat
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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Zoe is thinking..."):
            try:
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                
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
                
                # Add system instructions
                system_prompt = """You are Zoe, the premier cultural concierge at Omaha Performing Arts.

                You have impeccable taste and deep knowledge of the performing arts. Like a sommelier recommending the perfect pairing, you thoughtfully match guests with shows that suit their exact preferences and occasion.

                Speak with elegance and warmth. Each recommendation should feel personally curated.

                IMPORTANT: Recommend a maximum of 3 shows. If more options exist, mention that other choices are available but focus on your top 3 selections.

                Examples of your tone:
                - "For an evening that balances spectacle with substance, I'd recommend..."
                - "If you're seeking something that will resonate with the entire family..."
                - "Guests with your particular taste tend to appreciate..."
                - "Allow me to suggest three exceptional options..."

                After providing recommendations (maximum 3), ALWAYS ask ONE refined follow-up question to further personalize their experience:
                - "Will this be an intimate evening or a celebration with company?"
                - "Do you prefer something emotionally stirring or lighthearted?"
                - "Are you drawn to contemporary works or timeless classics?"

                You don't just list shows - you craft experiences."""

                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    tools=tools,
                    system=system_prompt, 
                    messages=[{"role": "user", "content": prompt}]
                )
                
                if message.stop_reason == "tool_use":
                    tool_use = next(block for block in message.content if block.type == "tool_use")
                    month = tool_use.input.get("month")
                    genre = tool_use.input.get("genre")
                    venue = tool_use.input.get("venue")
                    results = search_shows(month=month, genre=genre, venue=venue)
                    
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