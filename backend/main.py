from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routes.status_routes import router as status_router
from routes.diagnosis_routes import router as diagnosis_router
from routes.info_routes import router as info_router
from routes.status_routes import lifespan  # Import lifespan from status_routes

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Create FastAPI instance with lifespan event handler
app = FastAPI(lifespan=lifespan)  # Assign lifespan function to the app

# CORS setup - Allow requests from specific origins (frontend URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://harithkavish.github.io/SkinNet-Analyzer/", "https://harithkavish.github.io", "http://localhost:3000"],  # Update this if you need more origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers 
)

# Register routers with prefixes
app.include_router(status_router, prefix="/api")
app.include_router(diagnosis_router, prefix="/api")
app.include_router(info_router, prefix="/api")

# Optional: For running directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Default port 8000 for local development
    uvicorn.run(app, host="0.0.0.0", port=port)

# uvicorn main:app --reload
