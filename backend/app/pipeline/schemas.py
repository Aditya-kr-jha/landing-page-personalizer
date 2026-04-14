"""
Pipeline Input & Result Data schemas.

Internal domain schemas for sequencing the orchestrator. Contains no
HTTP-level concerns like status structures or detailed serialization overrides.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ad_agent.schemas import AdInput, AdAnalysis
from app.page_agent.schemas import PageInput, PageAnalysis
from app.renderer.schemas import RenderResult


class PipelineInput(BaseModel):
    """
    Combined input necessary to trigger the entire pipeline.
    Passed directly down to the ad and page agent in parallel.
    """

    ad_input: AdInput = Field(
        ...,
        description="The ad image or url provided as input.",
    )
    page_input: PageInput = Field(
        ...,
        description="The landing page to personalize.",
    )


class PipelineResult(BaseModel):
    """
    Final result constructed out of the orchestrator run.
    Contains everything required to represent the full trace
    and final HTML personalization.
    """

    ad_analysis: AdAnalysis = Field(
        ...,
        description="The ad analysis from Step 1.",
    )
    page_analysis: PageAnalysis = Field(
        ...,
        description="The page analysis from Step 2.",
    )
    render_result: RenderResult = Field(
        ...,
        description="The terminal result containing personalized HTML & audit trails.",
    )
