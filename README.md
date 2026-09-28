# Chimera-X Brain

Chimera-X is a local-first Personal AI Router and Memory System. It features a Next.js frontend and a FastAPI backend with SQLAlchemy, designed to decouple persistent "brain" memory from the underlying AI providers (Claude, OpenAI, Gemini, local Ollama, etc.).

## Project Structure

This repository contains two main components:

- **[`backend/`](backend/)**: The FastAPI application handling the LLM routing, memory, database operations, and API endpoints. 
- **[`frontend/`](frontend/)**: The Next.js web interface for interacting with the AI system.
- **[`docs/`](docs/)**: Project documentation and prompt history.
- **[`scripts/`](scripts/)**: Helper scripts for testing and automation.

## Quick Start

To run the full stack, you will need to start both the backend and frontend servers.

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   *The backend will be running at [http://localhost:8000](http://localhost:8000)*

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   *The frontend will be available at [http://localhost:3000](http://localhost:3000)*

## Key Features

- **Multi-Provider Router**: Seamlessly switches between different AI models and providers mid-conversation.
- **Auto-Fallback**: Automatically falls back to secondary models upon encountering rate limits or quota errors without losing context.
- **Persistent Memory**: The database acts as the single source of truth for conversational context, entirely agnostic to the AI model acting as the "mouth".

## Architecture Philosophy

> **Golden rule:** The model is a disposable "mouth." The brain (DB) is the only source of truth. Nothing about stored context, memory, or history may ever depend on which model generated it.

## License

MIT
