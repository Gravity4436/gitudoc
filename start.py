import uvicorn
import webbrowser
import threading
import time
import os
import sys

def open_browser():
    """Wait for server to start then open browser."""
    time.sleep(1.5) # Give server a moment to start
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("Starting GituDoc Server...")
    print("Please wait, browser will open automatically...")
    
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the server
    # We use 'main:app' assuming this script is in the same dir as main.py
    # reload=False for production/server mode
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
