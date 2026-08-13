import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from database import init_db, save_message, get_history, save_lesson_version, load_lesson_version, list_lesson_versions
from actions import action_save_version, action_list_versions
from query_rewriter import rewrite_query


def test_database_init():
    init_db()
    assert True


def test_save_and_get_history():
    save_message("pytest-session", "user", "Hello test")
    history = get_history("pytest-session")
    assert len(history) >= 1
    assert history[-1]["content"] == "Hello test"


def test_save_and_load_lesson_version():
    lesson = {"title": "Pytest Lesson"}
    version_id = save_lesson_version("pytest-session", "Test Topic", "beginner", lesson)
    assert version_id is not None

    loaded = load_lesson_version(version_id)
    assert loaded is not None
    assert loaded["lesson_json"]["title"] == "Pytest Lesson"


def test_list_lesson_versions():
    versions = list_lesson_versions("pytest-session")
    assert isinstance(versions, list)
    assert len(versions) >= 1


def test_action_save_version_returns_confirmation():
    result = action_save_version("pytest-session", "Another Topic", "beginner", {"title": "X"})
    assert "Saved as version" in result


def test_action_list_versions_returns_text():
    result = action_list_versions("pytest-session")
    assert isinstance(result, str)
    assert len(result) > 0


def test_rewrite_query_returns_original_if_no_history():
    result = rewrite_query([], "Generate a lesson on Python Loops")
    assert result == "Generate a lesson on Python Loops"