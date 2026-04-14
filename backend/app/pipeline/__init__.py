"""
Pipeline Module — Orchestrates the integration of the four standard 
operations into an end-to-end task generator.
"""

from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.schemas import PipelineInput, PipelineResult

__all__ = [
    "PipelineOrchestrator",
    "PipelineInput",
    "PipelineResult",
]
