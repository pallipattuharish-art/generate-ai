"""
Materials Blueprint for AI Study Assistant.
Handles saving, querying, retrieving, and deleting study materials and quiz results in SQLite.
"""

from flask import Blueprint, request, jsonify
from database import (
    save_material,
    get_all_materials,
    get_material_by_id,
    delete_material_by_id,
    save_quiz_result,
    get_all_quiz_results,
    get_study_stats
)

materials_bp = Blueprint("materials", __name__, url_prefix="/api")


@materials_bp.route("/materials", methods=["POST"])
def create_material():
    """Save generated study material to local SQLite database."""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    subject = (data.get("subject") or "General").strip()
    material_type = (data.get("material_type") or "notes").strip()
    content = data.get("content")
    source_snippet = (data.get("source_snippet") or "").strip()

    if not title:
        return jsonify({"success": False, "error": "Material title is required."}), 400
    if not content:
        return jsonify({"success": False, "error": "Material content cannot be empty."}), 400

    try:
        mat_id = save_material(
            title=title,
            subject=subject,
            material_type=material_type,
            content=content,
            source_snippet=source_snippet[:250] if source_snippet else None
        )
        return jsonify({
            "success": True,
            "id": mat_id,
            "message": "Study material successfully saved to your local library!"
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save material: {str(e)}"}), 500


@materials_bp.route("/materials", methods=["GET"])
def list_materials():
    """Retrieve saved materials with optional search query and type filter."""
    search_query = request.args.get("search", "").strip()
    material_type = request.args.get("type", "").strip()

    try:
        items = get_all_materials(search_query=search_query, material_type=material_type)
        return jsonify({
            "success": True,
            "materials": items,
            "count": len(items)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to query materials: {str(e)}"}), 500


@materials_bp.route("/materials/<int:material_id>", methods=["GET"])
def get_material(material_id: int):
    """Retrieve full details of a saved material by ID."""
    try:
        item = get_material_by_id(material_id)
        if not item:
            return jsonify({"success": False, "error": "Material not found."}), 404
        return jsonify({"success": True, "material": item}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to load material: {str(e)}"}), 500


@materials_bp.route("/materials/<int:material_id>", methods=["DELETE"])
def delete_material(material_id: int):
    """Delete a saved material item by ID."""
    try:
        success = delete_material_by_id(material_id)
        if not success:
            return jsonify({"success": False, "error": "Material not found or already deleted."}), 404
        return jsonify({"success": True, "message": "Material successfully deleted."}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to delete material: {str(e)}"}), 500


@materials_bp.route("/quiz-results", methods=["POST"])
def record_quiz_result():
    """Record a completed mock exam score and result breakdown."""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Mock Exam").strip()
    subject = (data.get("subject") or "General").strip()

    try:
        score = int(data.get("score", 0))
        total_questions = int(data.get("total_questions", 0))
        time_spent = int(data.get("time_spent_seconds", 0))
        details = data.get("details", [])

        if total_questions <= 0:
            return jsonify({"success": False, "error": "Total questions must be greater than 0."}), 400

        result_id = save_quiz_result(
            title=title,
            subject=subject,
            score=score,
            total_questions=total_questions,
            time_spent_seconds=time_spent,
            details=details
        )

        return jsonify({
            "success": True,
            "result_id": result_id,
            "message": "Quiz result recorded successfully!"
        }), 201
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to record quiz result: {str(e)}"}), 500


@materials_bp.route("/quiz-results", methods=["GET"])
def list_quiz_results():
    """Retrieve recent quiz history."""
    try:
        limit = int(request.args.get("limit", 20))
        results = get_all_quiz_results(limit=limit)
        return jsonify({"success": True, "results": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to fetch quiz results: {str(e)}"}), 500


@materials_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get aggregated dashboard metrics for study progress."""
    try:
        stats = get_study_stats()
        return jsonify({"success": True, "stats": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to calculate stats: {str(e)}"}), 500
