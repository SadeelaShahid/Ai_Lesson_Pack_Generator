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


def handle_message(session_id, message, level="beginner", duration_minutes=60):
    history = get_history(session_id)
    save_message(session_id, "user", message)

    route = decide_route(message)

    if "generate" in route:
        standalone_message = rewrite_query(history, message)
        result = generate_lesson_pack(standalone_message, level=level, duration_minutes=duration_minutes)
        LAST_LESSON[session_id] = {
            "topic": standalone_message,
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
    sid = "router-test-session"

    print("=== Test 1: Generate ===")
    r1 = handle_message(sid, "Generate a lesson on Python Loops")
    print(f"Route: {r1['route']}")
    print(f"Reply preview: {r1['reply'][:150]}...\n")

    print("=== Test 2: Save ===")
    r2 = handle_message(sid, "Save this lesson")
    print(f"Route: {r2['route']}")
    print(f"Reply: {r2['reply']}\n")

    print("=== Test 3: List ===")
    r3 = handle_message(sid, "Show me my saved lessons")
    print(f"Route: {r3['route']}")
    print(f"Reply: {r3['reply']}\n")

    print("=== Test 4: Chat ===")
    r4 = handle_message(sid, "Hello, how are you?")
    print(f"Route: {r4['route']}")
    print(f"Reply: {r4['reply']}\n")