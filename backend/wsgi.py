from main import app  # Import your Flask app
from waitress import serve

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)