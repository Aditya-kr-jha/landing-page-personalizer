"""
Page Agent — Scrapes a landing page URL, parses it into labeled sections,
and runs an LLM analysis chain that scores each section's CRO effectiveness.
"""

from app.page_agent.schemas import (
    PageAgentResult,
    PageAnalysis,
    PageInput,
    PageStructure,
)
from app.page_agent.service import PageAgentService

__all__ = [
    "PageAgentService",
    "PageInput",
    "PageAgentResult",
    "PageStructure",
    "PageAnalysis",
]
