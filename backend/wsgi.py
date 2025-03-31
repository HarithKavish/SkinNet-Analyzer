import os
from main import app
from waitress import serve

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use the dynamic PORT or default to 5000
    serve(app, host="0.0.0.0", port=port)
