import asyncio
import os
import sys

# Add backend to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.schemas import PipelineInput
from app.ad_agent.schemas import AdInput
from app.page_agent.schemas import PageInput
from app.config import settings

# Force fuzzy match to be true
settings.RENDERER_ENABLE_FUZZY_MATCHING = True
# Force threshold to 0 to prevent confidence blocking
settings.RENDERER_MIN_CONFIDENCE_THRESHOLD = 0.0

async def debug_pipeline():
    print("Initializing components...")
    orchestrator = PipelineOrchestrator()
    
    # We will test an actual input 
    pipeline_input = PipelineInput(
        ad_input=AdInput(
            ad_page_url="https://example.com/ad", 
            ad_image_base64=None, 
            ad_image_url=None
        ),
        page_input=PageInput(
            landing_page_url="https://example.com"
        )
    )

    print("Running pipeline...")
    result = await orchestrator.run(pipeline_input)
    render_result = result.render_result
    
    # Print the diagnostics
    print(f"\n--- DIAGNOSTICS ---")
    print(f"Edits Proposed by LLM: {len(result.render_result.guardrail_result.checks[0].blocked_section_ids) + len(result.render_result.edits_applied) + len(result.render_result.edits_skipped)}") 
    
    print(f"Edits Applied: {len(render_result.edits_applied)}")
    print(f"Edits Skipped: {len(render_result.edits_skipped)}")
    
    if render_result.edits_skipped:
        for skip in render_result.edits_skipped:
            print(f"  SKIPPED: {skip.section_id} - {skip.reason}")

    print(f"Warnings: {render_result.warnings}")

if __name__ == "__main__":
    asyncio.run(debug_pipeline())
