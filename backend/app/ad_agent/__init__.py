"""
Ad Agent — Analyzes ad creatives (image or URL) and extracts
structured messaging signals: offer, audience, tone, CTA, urgency.
"""

from app.ad_agent.schemas import AdAnalysis, AdInput
from app.ad_agent.service import AdAgentService

__all__ = ["AdAgentService", "AdInput", "AdAnalysis"]
