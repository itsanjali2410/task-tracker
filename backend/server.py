"""
Main entry point for the FastAPI application.
This file imports the app from the modular structure.
"""
from app.main import app

# This allows uvicorn to find the app when running:
# uvicorn server:app --reload
