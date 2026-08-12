import json
from database import save_lesson_version, load_lesson_version, list_lesson_versions


def action_save_version(session_id, topic, level, lesson_json):
    """Saves the current lesson as a new version and returns confirmation."""
    version_id = save_lesson_version(session_id, topic, level, lesson_json)
    return f"Saved as version #{version_id}."


def action_list_versions(session_id):
    """Lists all saved lesson versions for this session."""
    versions = list_lesson_versions(session_id)
    if not versions:
        return "No saved versions yet for this session."
    lines = [f"#{v['id']}: {v['topic']} ({v['level']}) - saved {v['created_at']}" for v in versions]
    return "\n".join(lines)


def action_load_version(version_id):
    """Loads a specific saved lesson version by its ID."""
    version = load_lesson_version(int(version_id))
    if version is None:
        return f"No version found with ID {version_id}."
    return json.dumps(version["lesson_json"], indent=2)


ACTIONS = {
    "save_version": action_save_version,
    "list_versions": action_list_versions,
    "load_version": action_load_version,
}


if __name__ == "__main__":
    sid = "test-actions-session"
    fake_lesson = {"title": "Test Lesson on Loops"}

    print(action_save_version(sid, "Python Loops", "beginner", fake_lesson))
    print(action_save_version(sid, "Python Loops (advanced)", "intermediate", fake_lesson))
    print("\n--- All versions ---")
    print(action_list_versions(sid))