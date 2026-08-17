# AI Lesson Pack Generator

Turns a short lesson outline into a complete, ready-to-teach lesson pack (learning objectives, explanations, examples, practice tasks, and a quiz) using RAG over provided course materials.

Built as a Week 6 Capstone Project for the Visionerds AI Engineering Internship.

## What It Does

A teacher gives a topic (e.g. "Python Loops") and the app generates a complete lesson pack grounded in the provided curriculum documents — not from the model's general knowledge. It also supports:

- Follow-up requests like "make the second example easier" or "create an advanced version"
- Saving and loading different versions of a generated lesson
- Honestly saying a topic isn't covered instead of inventing content

## How It Works (High-Level Flow)

User message
  -> Router decides: generate / save / list / load / chat
  -> If generate: rewrite vague follow-ups, retrieve relevant chunks (Chroma),
     build a lesson via the LLM, validate it's proper JSON
  -> Save conversation + lesson version to SQLite
  -> Return response as JSON

## Project Structure

app/
  main.py              FastAPI app (endpoints)
  router.py             Decides which path a message takes and orchestrates the response
  lesson_generator.py   RAG-based lesson generation (retrieval + LLM + JSON validation)
  query_rewriter.py     Rewrites vague follow-up questions into standalone ones
  vector_store.py       Chunking, embeddings, and Chroma vector store
  pdf_loader.py         Extracts text from the course material PDFs
  actions.py            Tools: save/list/load lesson versions
  database.py           SQLite: sessions, messages, lesson versions
  data/                 Course material PDFs + Chroma DB + SQLite DB (generated)
tests/
  test_app.py            Basic tests for database, actions, and query rewriting
.github/workflows/
  ci.yml                Runs tests automatically on every push

## Setup

1. Clone the repo and create a virtual environment:
   python -m venv venv
   source venv/Scripts/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Create a .env file in the project root (see .env.example):
   OPENROUTER_API_KEY=your_key_here

4. Build the vector store (one-time, or whenever the course materials change):
   cd app
   python vector_store.py

## Running the App

From the app folder:

uvicorn main:app --reload --port 8080

Then open http://127.0.0.1:8080/docs for an interactive API explorer (Swagger UI), or use curl/Postman.

## Example Usage

Generate a lesson:
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"demo-1\", \"message\": \"Generate a lesson on Python Loops\", \"level\": \"beginner\"}"

Follow-up (uses conversation memory):
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"demo-1\", \"message\": \"Make the second example easier\"}"

Save the last generated lesson:
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"session_id\": \"demo-1\", \"message\": \"Save this lesson\"}"

List saved versions for a session:
curl http://127.0.0.1:8080/versions/demo-1

## Running Tests

python -m pytest tests/ -v

Tests run automatically on every push via GitHub Actions (see .github/workflows/ci.yml).

## Known Limitations

- Uses OpenRouter's free-tier models, which occasionally return inconsistent responses. Retry logic is in place for the most important calls (routing and lesson JSON generation) to mitigate this.
- No frontend — interact via the Swagger UI (/docs), curl, or Postman.
-