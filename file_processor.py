"""
File processing module for AI Study Assistant.
Handles extracting readable text from PDF, DOCX, TXT, and Markdown files safely.
Detects scanned / image-only PDFs and informs users clearly.
"""

import os
from pathlib import Path
from werkzeug.utils import secure_filename
import pypdf
import docx
from config import Config


class FileProcessingError(Exception):
    """Custom exception for file processing errors."""
    pass


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def extract_text_from_pdf(filepath: Path) -> dict:
    """
    Extract text from a PDF file using pypdf.
    Detects if the PDF has scanned images / no selectable text.
    """
    try:
        reader = pypdf.PdfReader(str(filepath))
        num_pages = len(reader.pages)
        if num_pages == 0:
            raise FileProcessingError("The uploaded PDF has no pages.")

        extracted_pages = []
        total_text_length = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            cleaned = page_text.strip()
            total_text_length += len(cleaned)
            if cleaned:
                extracted_pages.append(f"--- Page {page_idx} ---\n{cleaned}")

        full_text = "\n\n".join(extracted_pages).strip()

        # If very few characters were extracted across multiple pages, likely scanned
        if total_text_length < 30 and num_pages > 0:
            return {
                "success": False,
                "text": "",
                "pages": num_pages,
                "error": (
                    "This PDF appears to contain scanned images or handwritten pages without "
                    "selectable digital text. OCR (Optical Character Recognition) is required "
                    "to extract text from scanned documents. Please upload a PDF with selectable "
                    "computer text or paste your notes directly."
                ),
                "is_scanned": True
            }

        return {
            "success": True,
            "text": full_text,
            "pages": num_pages,
            "word_count": len(full_text.split()),
            "character_count": len(full_text)
        }

    except pypdf.errors.PdfReadError as e:
        raise FileProcessingError(f"Corrupted or invalid PDF file: {str(e)}")
    except Exception as e:
        if isinstance(e, FileProcessingError):
            raise
        raise FileProcessingError(f"Error parsing PDF: {str(e)}")


def extract_text_from_docx(filepath: Path) -> dict:
    """Extract text from a DOCX file, including paragraphs and tables."""
    try:
        doc = docx.Document(str(filepath))
        parts = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)

        # Extract table contents if present
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    parts.append(row_text)

        full_text = "\n\n".join(parts).strip()
        if not full_text:
            return {
                "success": False,
                "text": "",
                "error": "The uploaded DOCX file does not contain any readable text."
            }

        return {
            "success": True,
            "text": full_text,
            "word_count": len(full_text.split()),
            "character_count": len(full_text)
        }
    except Exception as e:
        raise FileProcessingError(f"Error reading Word document: {str(e)}")


def extract_text_from_txt(filepath: Path) -> dict:
    """Extract text from plain text or markdown files."""
    try:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except UnicodeDecodeError:
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read().strip()

        if not content:
            return {
                "success": False,
                "text": "",
                "error": "The uploaded text file is empty."
            }

        return {
            "success": True,
            "text": content,
            "word_count": len(content.split()),
            "character_count": len(content)
        }
    except Exception as e:
        raise FileProcessingError(f"Error reading text file: {str(e)}")


def process_uploaded_file(file_storage, save_dir: Path) -> dict:
    """
    Save uploaded file securely, extract text, and cleanup the temporary file.
    """
    if not file_storage or not file_storage.filename:
        raise FileProcessingError("No file was selected for upload.")

    filename = secure_filename(file_storage.filename)
    if not filename:
        raise FileProcessingError("Invalid filename provided.")

    if not allowed_file(filename):
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "unknown"
        raise FileProcessingError(
            f"Unsupported file format (.{ext}). Supported formats: PDF, DOCX, TXT, MD."
        )

    save_dir.mkdir(parents=True, exist_ok=True)
    temp_path = save_dir / filename

    try:
        file_storage.save(temp_path)

        # Check file size (e.g. 0 bytes)
        if temp_path.stat().st_size == 0:
            raise FileProcessingError("The uploaded file is empty (0 bytes).")

        ext = filename.rsplit(".", 1)[1].lower()
        if ext == "pdf":
            result = extract_text_from_pdf(temp_path)
        elif ext == "docx":
            result = extract_text_from_docx(temp_path)
        elif ext in ("txt", "md"):
            result = extract_text_from_txt(temp_path)
        else:
            raise FileProcessingError(f"Unsupported extension: .{ext}")

        result["filename"] = filename
        return result

    finally:
        # Always clean up temporary uploaded file
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
