"""
Renderer — Validates the edit plan against guardrails and applies
text replacements to the landing page HTML, producing a personalized
page ready for frontend consumption.
"""

from app.renderer.schemas import RenderInput, RenderResult
from app.renderer.service import RendererService

__all__ = [
    "RendererService",
    "RenderInput",
    "RenderResult",
]
