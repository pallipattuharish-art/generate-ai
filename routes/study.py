"""
Study Blueprint for AI Study Assistant.
Handles AI-powered operations: Summarization, Concept Explanation (English & Telugu),
Practice Questions (MCQ, Short, Long), Flashcards generation, and Mock Tests.
"""

from flask import Blueprint, request, jsonify
from ai_service import AIService, AIServiceError
import prompts

study_bp = Blueprint("study", __name__, url_prefix="/api")
ai_service = AIService()

MAX_INPUT_CHARS = 100000  # Guardrail against unreasonably huge input payload


def validate_notes_payload(data: dict) -> tuple[str, str, str]:
    """Validate common note fields and return cleaned values."""
    notes = (data.get("notes") or "").strip()
    if not notes:
        raise ValueError("Please provide or paste your study notes before generating content.")
    if len(notes) > MAX_INPUT_CHARS:
        raise ValueError(f"Notes text exceeds the maximum limit of {MAX_INPUT_CHARS:,} characters.")
    subject = (data.get("subject") or "").strip()
    topic = (data.get("topic") or "").strip()
    return notes, subject, topic


@study_bp.route("/status", methods=["GET"])
def get_status():
    """Return AI service status without exposing credentials."""
    status = ai_service.get_provider_status()
    return jsonify({"success": True, "status": status})


@study_bp.route("/summarize", methods=["POST"])
def summarize_notes():
    """Generate structured revision summary from study notes."""
    data = request.get_json(silent=True) or {}
    try:
        notes, subject, topic = validate_notes_payload(data)
        length_mode = data.get("length", "medium").lower()
        if length_mode not in ("short", "medium", "detailed"):
            length_mode = "medium"

        sys_prompt, usr_prompt = prompts.build_summary_prompt(
            notes_text=notes,
            length_mode=length_mode,
            subject=subject,
            topic=topic
        )

        result = ai_service.generate_text(sys_prompt, usr_prompt)
        return jsonify({
            "success": True,
            "summary": result["text"],
            "is_demo": result["is_demo"],
            "provider": result["provider"],
            "model": result["model"],
            "length": length_mode
        }), 200

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except AIServiceError as ae:
        return jsonify({"success": False, "error": str(ae)}), 502
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@study_bp.route("/explain", methods=["POST"])
def explain_concept():
    """Explain a complex concept with selectable depth and language (English / Telugu)."""
    data = request.get_json(silent=True) or {}
    try:
        concept = (data.get("concept") or "").strip()
        if not concept:
            return jsonify({"success": False, "error": "Please enter a concept or question to explain."}), 400

        level = data.get("level", "beginner").lower()
        if level not in ("beginner", "intermediate", "advanced"):
            level = "beginner"

        language = data.get("language", "english").lower()
        if language not in ("english", "telugu"):
            language = "english"

        notes_context = (data.get("notes") or "").strip()
        if len(notes_context) > MAX_INPUT_CHARS:
            notes_context = notes_context[:MAX_INPUT_CHARS]

        sys_prompt, usr_prompt = prompts.build_concept_explanation_prompt(
            concept=concept,
            level=level,
            language=language,
            notes_context=notes_context
        )

        result = ai_service.generate_text(sys_prompt, usr_prompt)
        return jsonify({
            "success": True,
            "concept": concept,
            "explanation": result["text"],
            "level": level,
            "language": language,
            "is_demo": result["is_demo"],
            "provider": result["provider"],
            "model": result["model"]
        }), 200

    except AIServiceError as ae:
        return jsonify({"success": False, "error": str(ae)}), 502
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@study_bp.route("/questions", methods=["POST"])
def generate_questions():
    """Generate practice questions (MCQ, Short-Answer, Long-Answer)."""
    data = request.get_json(silent=True) or {}
    try:
        notes, subject, _ = validate_notes_payload(data)
        num_questions = int(data.get("num_questions", 5))
        if num_questions not in (5, 10, 20):
            num_questions = 5

        difficulty = data.get("difficulty", "medium").lower()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        q_type = data.get("q_type", "mcq").lower()
        if q_type not in ("mcq", "short", "long"):
            q_type = "mcq"

        sys_prompt, usr_prompt = prompts.build_questions_prompt(
            notes_text=notes,
            num_questions=num_questions,
            difficulty=difficulty,
            q_type=q_type,
            subject=subject
        )

        result = ai_service.generate_json(sys_prompt, usr_prompt)
        return jsonify({
            "success": True,
            "data": result["data"],
            "is_demo": result["is_demo"],
            "provider": result["provider"],
            "model": result["model"],
            "q_type": q_type,
            "difficulty": difficulty
        }), 200

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except AIServiceError as ae:
        return jsonify({"success": False, "error": str(ae)}), 502
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@study_bp.route("/flashcards", methods=["POST"])
def generate_flashcards():
    """Generate revision flashcards from study notes."""
    data = request.get_json(silent=True) or {}
    try:
        notes, subject, _ = validate_notes_payload(data)
        count = int(data.get("count", 10))
        if count not in (5, 10, 15, 20):
            count = 10

        sys_prompt, usr_prompt = prompts.build_flashcards_prompt(
            notes_text=notes,
            count=count,
            subject=subject
        )

        result = ai_service.generate_json(sys_prompt, usr_prompt)
        cards = result["data"].get("flashcards", [])
        return jsonify({
            "success": True,
            "flashcards": cards,
            "total_cards": len(cards),
            "is_demo": result["is_demo"],
            "provider": result["provider"],
            "model": result["model"]
        }), 200

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except AIServiceError as ae:
        return jsonify({"success": False, "error": str(ae)}), 502
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500


@study_bp.route("/mock-test", methods=["POST"])
def generate_mock_test():
    """Generate structured mock exam with 4-choice MCQs and rationales."""
    data = request.get_json(silent=True) or {}
    try:
        notes, subject, _ = validate_notes_payload(data)
        num_questions = int(data.get("num_questions", 10))
        if num_questions not in (5, 10, 15, 20):
            num_questions = 10

        difficulty = data.get("difficulty", "medium").lower()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        sys_prompt, usr_prompt = prompts.build_mock_test_prompt(
            notes_text=notes,
            num_questions=num_questions,
            difficulty=difficulty,
            subject=subject
        )

        result = ai_service.generate_json(sys_prompt, usr_prompt)
        test_payload = result["data"]
        return jsonify({
            "success": True,
            "test_data": test_payload,
            "is_demo": result["is_demo"],
            "provider": result["provider"],
            "model": result["model"]
        }), 200

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except AIServiceError as ae:
        return jsonify({"success": False, "error": str(ae)}), 502
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500
