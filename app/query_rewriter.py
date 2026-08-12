import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def rewrite_query(history, new_message):
    if not history:
        return new_message

    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history[-6:]])

    prompt = f"""Given this conversation history:
{history_text}

And this new message: "{new_message}"

If the new message is a vague follow-up (like "make it easier", "the second one", "what about X"),
rewrite it into a standalone request that includes the necessary context from the conversation.
If it is already clear and standalone, return it unchanged.

Only output the rewritten message, nothing else."""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    fake_history = [
        {"role": "user", "content": "Generate a beginner lesson on Python Loops"},
        {"role": "assistant", "content": "Here is your lesson pack on Python Loops, with 2 examples."},
    ]

    test1 = "make the second example easier"
    print(f"Original: {test1}")
    print(f"Rewritten: {rewrite_query(fake_history, test1)}\n")

    test2 = "create an advanced version instead"
    print(f"Original: {test2}")
    print(f"Rewritten: {rewrite_query(fake_history, test2)}\n")

    test3 = "Generate a lesson on SQL joins"
    print(f"Original: {test3}")
    print(f"Rewritten: {rewrite_query(fake_history, test3)}")