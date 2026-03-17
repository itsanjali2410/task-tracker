"""
Main entry point for the FastAPI application.
This file imports the app from the modular structure.
"""
from src.app.main import app

# This allows uvicorn to find the app when running:
# uvicorn src.app.main:app --reload
