import streamlit as st
import anthropic
from function import search_shows
import json

# Page config
st.set_page_config(
    page_title="Zoe - OPA Concierge",
    page_icon="🎭",
    layout="wide"
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

# Create API endpoint for the HTML to call
if "query" in st.query_params:
    # This handles requests from the embedded HTML
    question = st.query_params.get("query", "")
    
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
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=[{"role": "user", "content": question}]
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
                    {"role": "user", "content": question},
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
        
        # Return answer as JSON
        st.json({"answer": answer})
        st.stop()
        
    except Exception as e:
        st.json({"error": str(e)})
        st.stop()

# Embed your custom HTML interface
st.components.v1.html("""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .chat-container {
            width: 100%;
            max-width: 430px;
            height: 95vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #7B3FF2 0%, #9B59B6 100%);
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 18px;
            font-weight: 600;
        }
        .welcome {
            text-align: center;
            padding: 40px 20px;
        }
        .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #7B3FF2 0%, #9B59B6 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
        }
        .welcome h2 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #333;
        }
        .welcome p {
            color: #666;
            font-size: 14px;
        }
        #chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        .user {
            background: linear-gradient(135deg, #7B3FF2 0%, #9B59B6 100%);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .agent {
            background: #f0f0f0;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            white-space: pre-wrap;
        }
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
        }
        .input-wrapper {
            display: flex;
            gap: 10px;
            align-items: center;
            background: #f5f5f5;
            border-radius: 25px;
            padding: 8px 8px 8px 20px;
        }
        #question {
            flex: 1;
            border: none;
            background: transparent;
            font-size: 15px;
            outline: none;
            color: #333;
        }
        #question::placeholder {
            color: #999;
        }
        #send-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #7B3FF2 0%, #9B59B6 100%);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: transform 0.2s;
        }
        #send-btn:hover {
            transform: scale(1.05);
        }
        #send-btn:active {
            transform: scale(0.95);
        }
        .welcome.hidden {
            display: none;
        }
        .typing {
            padding: 12px 16px;
            background: #f0f0f0;
            border-radius: 18px;
            max-width: 80px;
            align-self: flex-start;
        }
        .typing span {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">Zoe - Your OPA Guide</div>
        <div class="welcome" id="welcome">
            <div class="avatar">🎭</div>
            <h2>Hi! I'm Zoe</h2>
            <p>Your personal guide to Omaha Performing Arts.<br>Ask me about shows, dates, or venues!</p>
        </div>
        <div id="chat-box"></div>
        <div class="input-container">
            <div class="input-wrapper">
                <input type="text" id="question" placeholder="Ask about shows...">
                <button id="send-btn">➤</button>
            </div>
        </div>
    </div>
    <script>
        const chatBox = document.getElementById('chat-box');
        const questionInput = document.getElementById('question');
        const sendBtn = document.getElementById('send-btn');
        const welcome = document.getElementById('welcome');
        
        setTimeout(() => {
            addMessage("Hi! I'm Zoe, your personal guide to Omaha Performing Arts! 🎭\\n\\nI can help you find shows by month, genre, or venue. What are you looking for today?", 'agent');
            welcome.classList.add('hidden');
        }, 1000);
        
        async function sendMessage() {
            const question = questionInput.value.trim();
            if (!question) return;
            
            welcome.classList.add('hidden');
            addMessage(question, 'user');
            questionInput.value = '';
            
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing';
            typingDiv.innerHTML = '<span></span><span></span><span></span>';
            chatBox.appendChild(typingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
            
            try {
                const response = await fetch(window.location.origin + '/?query=' + encodeURIComponent(question));
                const data = await response.json();
                typingDiv.remove();
                addMessage(data.answer, 'agent');
            } catch (error) {
                typingDiv.remove();
                addMessage('Sorry, I couldn\\'t reach the server. Please try again.', 'agent');
            }
        }
        
        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            messageDiv.textContent = text;
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        sendBtn.addEventListener('click', sendMessage);
        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
""", height=800, scrolling=False)