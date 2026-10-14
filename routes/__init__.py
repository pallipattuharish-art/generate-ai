"""
Routes package initialization for AI Study Assistant.
Registers blueprints for uploads, AI study tools, and saved materials.
"""

from .uploads import uploads_bp
from .study import study_bp
from .materials import materials_bp

__all__ = ["uploads_bp", "study_bp", "materials_bp"]
