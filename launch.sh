#!/bin/bash
# Launch Flask App - Works from any directory

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detect if we're in repo root or my-flask-app
if [ -d "$SCRIPT_DIR/my-flask-app" ]; then
    # We're in repo root
    REPO_ROOT="$SCRIPT_DIR"
    APP_DIR="$SCRIPT_DIR/my-flask-app"
elif [ -f "$SCRIPT_DIR/app/__init__.py" ]; then
    # We're in my-flask-app directory
    APP_DIR="$SCRIPT_DIR"
    REPO_ROOT="$(dirname "$SCRIPT_DIR")"
else
    echo "Error: Could not find Flask app. Run from repo root or my-flask-app folder."
    exit 1
fi

echo "Starting Flask app..."
echo "App directory: $APP_DIR"

cd "$APP_DIR"

# Check if virtual environment exists
VENV_PATH="$REPO_ROOT/.venv"
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo "Warning: Virtual environment not found at $VENV_PATH"
fi

# Set Flask app
export FLASK_APP=app
export FLASK_ENV=development

echo "Launching Flask development server..."
echo "Open your browser at http://127.0.0.1:5000"
echo ""

flask run
