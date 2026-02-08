# LeedsHack2026

## Background information
Task
What systems could be rebooted to unlock better learning?
Improve an existing system or process OR create a new system to solve a
learning related problem.

## Resources
Please see more details about the products we have built:
https://genio.co/notes
https://genio.co/present
https://genio.co/the-confident-notetakers-masterclass

## Starting Points
A system to address a time management or productivity problem in a playful, novel
way.

## Judging Criteria
Tech for good: solve a problem, benefit mental health, inform, enrich or teach
Playful: whimsy, entertaining, creative interpretation

---

## Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Apps

### Flask App (Port 5000) DEFUNCT DO NOT USE

**Option 1: Using launch script (Windows)**
```powershell
.\launch.ps1
```

**Option 2: Using launch script (macOS/Linux)**
```bash
chmod +x launch.sh
./launch.sh
```

**Option 3: Manual**
```bash
cd my-flask-app
set FLASK_APP=app  # Windows
export FLASK_APP=app  # macOS/Linux
flask run
```

Access at: **http://127.0.0.1:5000**

### FastAPI App (Port 8000)

**Option 1: Using launch script (Windows)**
```powershell
.\launch-fastapi.ps1
```

**Option 2: Using launch script (macOS/Linux)**
```bash
chmod +x launch-fastapi.sh
./launch-fastapi.sh
```

**Option 3: Manual**
```bash
cd my-fastapi-app
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Access at: **http://127.0.0.1:8000**

API docs: **http://127.0.0.1:8000/docs**

## Project Structure

```
LeedsHack2026/
├── my-fastapi-app/         # FastAPI version
│   ├── app/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   │   ├── style.css
│   │   └── main.js
├── mindmap_chat/           # AI backend for mind map generation
├── launch.ps1              # Flask launcher (Windows)
├── launch.sh               # Flask launcher (macOS/Linux)
├── launch-fastapi.ps1      # FastAPI launcher (Windows)
├── launch-fastapi.sh       # FastAPI launcher (macOS/Linux)
└── README.md
└── requirements.txt
```

## Features

- **3-Panel Interactive UI**
  - Left: Mindmap selector
  - Middle: Mindmap visualization (D3.js force-directed graph)
  - Right: AI chat interface
  
- **Resizable Panels**: Drag dividers to customize layout
- **Dummy Data**: Pre-loaded with sample mindmaps and chat messages
- **Bootstrap UI**: Responsive design with Bootstrap 5.2.3

## Framework Comparison

| Feature | Flask | FastAPI |
|---------|-------|---------|
| Port | 5000 | 8000 |
| Speed | Slower | Faster |
| Async | Limited | Native |
| Auto API Docs | No | Yes (/docs) |
| Type Hints | Manual | Built-in validation |

Both apps serve identical UI for comparison purposes.


