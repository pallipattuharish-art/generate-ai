"""
Uploads Blueprint for AI Study Assistant.
Handles secure file uploads, validation, and text extraction for PDF, DOCX, TXT, and MD files.
"""

from flask import Blueprint, request, jsonify
from config import Config
from file_processor import process_uploaded_file, FileProcessingError

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api")


@uploads_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle document uploads and text extraction."""
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": "No file part in the request. Please choose a document to upload."
        }), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "No file was selected. Please choose a PDF, DOCX, TXT, or MD file."
        }), 400

    try:
        result = process_uploaded_file(file, Config.UPLOAD_FOLDER)
        if not result.get("success", False):
            # Scanned PDF or empty document
            return jsonify({
                "success": False,
                "error": result.get("error", "Unable to extract readable text."),
                "is_scanned": result.get("is_scanned", False),
                "pages": result.get("pages", 0)
            }), 422

        return jsonify({
            "success": True,
            "filename": result.get("filename"),
            "text": result.get("text"),
            "pages": result.get("pages"),
            "word_count": result.get("word_count"),
            "character_count": result.get("character_count")
        }), 200

    except FileProcessingError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An unexpected error occurred while processing the file: {str(e)}"
        }), 500
