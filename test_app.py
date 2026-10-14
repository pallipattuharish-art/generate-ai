"""
Automated integration tests for AI Study Assistant Flask application and API routes.
"""

import io
import json
import pytest
from app import create_app
from config import TestConfig
from database import init_db


@pytest.fixture
def app(tmp_path):
    """Create test application configured with an isolated temporary SQLite database."""
    test_db = tmp_path / "test.db"
    TestConfig.DATABASE_PATH = test_db
    TestConfig.UPLOAD_FOLDER = tmp_path / "uploads"
    TestConfig.INSTANCE_PATH = tmp_path / "instance"

    app = create_app(TestConfig)
    init_db(test_db)
    yield app


@pytest.fixture
def client(app):
    """Test client fixture."""
    return app.test_client()


# ==================== Page Routes ====================
def test_pages_render_successfully(client):
    """Ensure all core web pages render with HTTP 200."""
    routes = ["/", "/dashboard", "/study", "/saved", "/health"]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Route {route} failed with {response.status_code}"


def test_health_endpoint(client):
    """Verify health endpoint returns JSON with database and AI status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


# ==================== Core Feature 1: File Upload ====================
def test_upload_valid_text_file(client):
    """Verify text file upload and extraction via API."""
    file_content = b"Data structures: Arrays provide contiguous indexing O(1)."
    data = {
        "file": (io.BytesIO(file_content), "test_notes.txt")
    }
    res = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "Data structures" in json_data["text"]
    assert json_data["word_count"] > 0


def test_upload_empty_request(client):
    """Verify 400 error when no file is included in upload."""
    res = client.post("/api/upload", data={}, content_type="multipart/form-data")
    assert res.status_code == 400
    assert res.get_json()["success"] is False


# ==================== Core Feature 2: Summarizer ====================
def test_summarize_notes_endpoint(client):
    """Verify notes summarizer generates structured summary."""
    payload = {
        "notes": "A binary heap is a complete binary tree that satisfies the heap property.",
        "length": "medium",
        "subject": "Algorithms",
        "topic": "Binary Heaps"
    }
    res = client.post("/api/summarize", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "summary" in data
    assert len(data["summary"]) > 0


def test_summarize_empty_notes(client):
    """Verify error when notes are empty."""
    res = client.post("/api/summarize", json={"notes": ""})
    assert res.status_code == 400
    assert res.get_json()["success"] is False


# ==================== Core Feature 3: Concept Explainer ====================
def test_explain_concept_english(client):
    """Verify concept explainer in English."""
    payload = {
        "concept": "Binary Search",
        "level": "beginner",
        "language": "english",
        "notes": "Binary search divides the sorted array in half."
    }
    res = client.post("/api/explain", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "Binary Search" in data["concept"]
    assert len(data["explanation"]) > 0


def test_explain_concept_telugu(client):
    """Verify concept explainer in Telugu (తెలుగు)."""
    payload = {
        "concept": "Recursion",
        "level": "beginner",
        "language": "telugu",
        "notes": "A function calling itself until a base condition is met."
    }
    res = client.post("/api/explain", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["language"] == "telugu"
    assert len(data["explanation"]) > 0


# ==================== Core Feature 4: Practice Questions ====================
def test_practice_questions_mcq(client):
    """Verify practice question generation for MCQs."""
    payload = {
        "notes": "A Stack is a Last-In First-Out (LIFO) data structure. Push and pop operate in O(1).",
        "num_questions": 5,
        "difficulty": "medium",
        "q_type": "mcq",
        "subject": "Data Structures"
    }
    res = client.post("/api/questions", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["type"] == "mcq"
    assert len(data["data"]["questions"]) > 0


def test_practice_questions_short(client):
    """Verify practice question generation for short-answer questions."""
    payload = {
        "notes": "Database normalization removes redundancy and update anomalies.",
        "num_questions": 5,
        "difficulty": "medium",
        "q_type": "short",
        "subject": "DBMS"
    }
    res = client.post("/api/questions", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["type"] == "short"


def test_practice_questions_long(client):
    """Verify practice question generation for long-answer essay questions."""
    payload = {
        "notes": "The OSI model consists of 7 layers from Physical to Application.",
        "num_questions": 5,
        "difficulty": "hard",
        "q_type": "long",
        "subject": "Computer Networks"
    }
    res = client.post("/api/questions", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["type"] == "long"


# ==================== Core Feature 5: Flashcards ====================
def test_flashcards_generation(client):
    """Verify revision flashcards generation."""
    payload = {
        "notes": "Operating systems manage CPU scheduling, virtual memory, and file systems.",
        "count": 5,
        "subject": "Operating Systems"
    }
    res = client.post("/api/flashcards", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["flashcards"]) > 0
    assert "front" in data["flashcards"][0]
    assert "back" in data["flashcards"][0]


# ==================== Core Feature 6: Mock Test ====================
def test_mock_test_generation(client):
    """Verify mock test generation with 4-choice options and answers."""
    payload = {
        "notes": "Computer Networks: TCP provides reliable byte stream transfer while UDP is connectionless.",
        "num_questions": 5,
        "difficulty": "medium",
        "subject": "Computer Networks"
    }
    res = client.post("/api/mock-test", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    test_data = data["test_data"]
    assert len(test_data["questions"]) > 0
    assert "correct_answer" in test_data["questions"][0]


# ==================== Core Feature 7: Saved Materials & SQLite CRUD ====================
def test_saved_materials_crud(client):
    """Verify full CRUD lifecycle for saved study materials in SQLite."""
    # 1. Create
    save_payload = {
        "title": "Data Structures Quick Review",
        "subject": "Computer Science",
        "material_type": "summary",
        "content": "# Quick Review\nArrays and Linked Lists.",
        "source_snippet": "Arrays and Linked Lists"
    }
    create_res = client.post("/api/materials", json=save_payload)
    assert create_res.status_code == 201
    created = create_res.get_json()
    mat_id = created["id"]
    assert mat_id > 0

    # 2. List & Search
    list_res = client.get("/api/materials?search=Data+Structures")
    assert list_res.status_code == 200
    items = list_res.get_json()["materials"]
    assert any(item["id"] == mat_id for item in items)

    # 3. Retrieve by ID
    get_res = client.get(f"/api/materials/{mat_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["material"]["title"] == "Data Structures Quick Review"

    # 4. Delete
    del_res = client.delete(f"/api/materials/{mat_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

    # 5. Verify deleted
    get_again = client.get(f"/api/materials/{mat_id}")
    assert get_again.status_code == 404


def test_quiz_results_and_stats(client):
    """Verify mock test score recording and aggregated dashboard statistics."""
    quiz_payload = {
        "title": "Midterm Mock Test",
        "subject": "Operating Systems",
        "score": 4,
        "total_questions": 5,
        "time_spent_seconds": 180,
        "details": [{"q": 1, "correct": True}]
    }
    post_res = client.post("/api/quiz-results", json=quiz_payload)
    assert post_res.status_code == 201

    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats = stats_res.get_json()["stats"]
    assert stats["total_quizzes"] >= 1
    assert stats["avg_score"] >= 80.0
