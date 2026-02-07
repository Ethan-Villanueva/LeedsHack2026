from fastapi import Request
from fastapi.responses import HTMLResponse
from app import app, templates


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page with dummy mindmaps and messages."""
    
    # Dummy mindmaps
    mindmaps = [
        {'id': 1, 'title': 'Machine Learning'},
        {'id': 2, 'title': 'Web Development'},
        {'id': 3, 'title': 'Python Tips'},
        {'id': 4, 'title': 'AI Ethics'},
        {'id': 5, 'title': 'Cloud Computing'}
    ]
    
    # Dummy chat messages
    messages = [
        {'sender': 'bot', 'text': 'Hi! I\'m your AI assistant. Choose a mindmap and let\'s learn together!', 'timestamp': 'Just now'},
        {'sender': 'user', 'text': 'Tell me about Machine Learning', 'timestamp': '2 min ago'},
        {'sender': 'bot', 'text': 'Machine Learning is a subset of AI where systems learn from data patterns. Key concepts include supervised learning, unsupervised learning, and reinforcement learning.', 'timestamp': '1 min ago'}
    ]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "mindmaps": mindmaps,
        "messages": messages
    })
