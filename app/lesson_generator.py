import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from vector_store import retrieve

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def build_context(topic, k=5):
    results = retrieve(topic, k=k)
    context_parts = []
    sources = set()
    for text, meta, distance in results:
        context_parts.append(f"[Source: {meta['source']}]\n{text}")
        sources.add(meta["source"])
    return "\n\n---\n\n".join(context_parts), list(sources)


def generate_lesson_pack(topic, level="beginner", duration_minutes=60):
    context, sources = build_context(topic, k=6)

    prompt = f"""You are an assistant that creates lesson packs for teachers, based ONLY on the course material provided below.

Course Material:
{context}

Task: Create a complete lesson pack for the topic "{topic}", level "{level}", duration {duration_minutes} minutes.

Respond with ONLY a valid JSON object in this exact structure, no extra text before or after:
{{
  "title": "...",
  "learning_objectives": ["...", "..."],
  "lesson_sections": [
    {{"heading": "...", "explanation": "...", "example": "..."}}
  ],
  "practice": ["...", "..."],
  "quiz": [
    {{"question": "...", "answer": "..."}}
  ]
}}

If the course material does not cover this topic, respond with:
{{"error": "Topic not covered in provided materials"}}
"""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_output = response.choices[0].message.content

    try:
        lesson_json = json.loads(raw_output)
    except json.JSONDecodeError:
        cleaned = raw_output.strip().strip("```").replace("json", "", 1).strip()
        try:
            lesson_json = json.loads(cleaned)
        except json.JSONDecodeError:
            return {"error": "Model did not return valid JSON", "raw_output": raw_output}

    lesson_json["sources"] = sources
    return lesson_json


if __name__ == "__main__":
    result = generate_lesson_pack("Python Loops", level="beginner", duration_minutes=60)
    print(json.dumps(result, indent=2))