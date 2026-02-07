from flask import render_template
from app import app

@app.route('/')
def home():
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
    
    return render_template('index.html', mindmaps=mindmaps, messages=messages)