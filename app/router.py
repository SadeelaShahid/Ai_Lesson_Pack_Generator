import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI

from lesson_generator import generate_lesson_pack
from query_rewriter import rewrite_query
from actions import action_save_version, action_list_versions, action_load_version
from database import save_message, get_history

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Keeps the most recently generated lesson's TOPIC (clean, short) per session,
# plus its full lesson JSON, so follow-ups can retrieve against the right topic.
LAST_LESSON = {}


def safe_chat_reply(message, max_retries=3):
    for attempt in range(max_retries):
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": "You are a friendly assistant for a lesson pack generator tool. Keep replies short and relevant to what the user actually said."},
                {"role": "user", "content": message}
            ]
        )
        content = response.choices[0].message.content

        if content is None or content.strip() == "":
            continue

        if len(content) > 500 and "user profile" in content.lower():
            continue

        return content

    return "Sorry, I couldn't generate a reply right now. Please try again."


def decide_route(message):
    routing_prompt = f"""Classify this message into exactly one category:

- "generate": the user wants a new or modified lesson pack created (e.g. "generate a lesson on X", "make the second example easier", "create an advanced version")
- "save": the user wants to save the current lesson (e.g. "save this", "save it as a version")
- "list": the user wants to see saved lesson versions (e.g. "show my saved lessons", "list versions")
- "load": the user wants to load a specific saved version (e.g. "load version 2", "show me version 3")
- "chat": anything else, like greetings or general questions (e.g. "hello", "thanks")

Message: "{message}"

Reply with ONLY one word: generate, save, list, load, or chat."""

    valid_routes = ["generate", "save", "list", "load", "chat"]

    for attempt in range(3):
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": routing_prompt}]
        )
        content = response.choices[0].message.content

        if content is None or content.strip() == "":
            continue

        cleaned = content.strip().lower()

        for valid_route in valid_routes:
            if valid_route in cleaned:
                return valid_route

    return "chat"


def extract_version_id(message):
    match = re.search(r"\d+", message)
    return match.group() if match else None


def extract_topic(message, history):
    """
    Decides what topic to retrieve course material for.
    If this looks like a fresh topic request, extract the topic from the message itself.
    If it looks like a follow-up modification and we have a previous topic for this
    session, reuse that previous topic for retrieval.
    """
    prompt = f"""The user said: "{message}"

Extract just the core subject/topic they want a lesson about (e.g. "Python Loops", "SQL JOIN and GROUP BY").
If the message does not mention a new topic and is instead a follow-up modification request
(like "make it easier", "the second example", "an advanced version instead"), reply with exactly: SAME_TOPIC

Reply with ONLY the topic name or SAME_TOPIC, nothing else."""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    return content.strip() if content else "SAME_TOPIC"


def handle_message(session_id, message, level="beginner", duration_minutes=60):
    history = get_history(session_id)
    save_message(session_id, "user", message)

    route = decide_route(message)

    if "generate" in route:
        extracted = extract_topic(message, history)

        if extracted == "SAME_TOPIC" and session_id in LAST_LESSON:
            topic = LAST_LESSON[session_id]["topic"]
        else:
            topic = extracted

        instruction = rewrite_query(history, message)

        result = generate_lesson_pack(
            topic,
            level=level,
            duration_minutes=duration_minutes,
            instruction=instruction
        )

        LAST_LESSON[session_id] = {
            "topic": topic,
            "level": level,
            "lesson_json": result
        }
        reply = json.dumps(result)

    elif "save" in route:
        if session_id not in LAST_LESSON:
            reply = "There is no generated lesson yet to save. Generate one first."
        else:
            saved = LAST_LESSON[session_id]
            reply = action_save_version(session_id, saved["topic"], saved["level"], saved["lesson_json"])

    elif "list" in route:
        reply = action_list_versions(session_id)

    elif "load" in route:
        version_id = extract_version_id(message)
        if version_id is None:
            reply = "Please specify a version number to load, e.g. 'load version 2'."
        else:
            reply = action_load_version(version_id)

    else:
        reply = safe_chat_reply(message)

    save_message(session_id, "assistant", reply)
    return {"route": route, "reply": reply}


if __name__ == "__main__":
    sid = "router-test-session-2"

    print("=== Test 1: Generate ===")
    r1 = handle_message(sid, "Generate a lesson on Python Loops")
    print(f"Route: {r1['route']}")
    print(f"Reply preview: {r1['reply'][:150]}...\n")

    print("=== Test 2: Follow-up (should reuse Python Loops topic) ===")
    r2 = handle_message(sid, "Make the second example easier")
    print(f"Route: {r2['route']}")
    print(f"Reply preview: {r2['reply'][:200]}...\n")