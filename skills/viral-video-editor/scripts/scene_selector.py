"""
scene_selector.py

Select the best video segments for a viral reel using the ViralScorer.
This is the orchestrator script that ties analyzer + scorer together.
"""

import logging
from pathlib import Path
from typing import Optional

from video_analyzer import GeminiVideoAnalyzer, SceneSegment, VideoAnalysis
from viral_scorer import ViralScorer

logger = logging.getLogger(__name__)


def select_best_scenes(
    video_path: str,
    min_duration: float = 45.0,
    max_duration: float = 90.0,
    reference_embeddings: Optional[list[list[float]]] = None,
    api_key: Optional[str] = None,
) -> tuple[VideoAnalysis, list[SceneSegment]]:
    """
    Full pipeline: analyze video → score segments → return best scenes.

    Args:
        video_path: Path to the input video file
        min_duration: Minimum reel duration in seconds (default 45)
        max_duration: Maximum reel duration in seconds (default 90)
        reference_embeddings: Optional list of viral reference embeddings
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)

    Returns:
        (VideoAnalysis, list of selected SceneSegments sorted chronologically)
    """
    logger.info(f"Scene selection started for: {video_path}")

    analyzer = GeminiVideoAnalyzer(api_key=api_key)
    analysis = analyzer.analyze(video_path)

    scorer = ViralScorer(reference_embeddings=reference_embeddings)
    scored_segments = scorer.score_analysis(analysis)

    selected = scorer.select_segments_for_reel(
        scored_segments,
        min_duration=min_duration,
        max_duration=max_duration,
    )

    total_selected_duration = sum(s.end_time - s.start_time for s in selected)
    logger.info(
        f"Selected {len(selected)} segments, total duration: {total_selected_duration:.1f}s"
    )

    # Log top 5 scores
    for s in scored_segments[:5]:
        seg = s.segment
        logger.info(
            f"  [{seg.virality_score:.1f}] {seg.start_time:.1f}s-{seg.end_time:.1f}s "
            f"'{seg.transcript[:60]}...'"
        )

    return analysis, selected


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python scene_selector.py <video_path> [min_duration] [max_duration]")
        sys.exit(1)
    vpath = sys.argv[1]
    mn = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
    mx = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0
    _, scenes = select_best_scenes(vpath, min_duration=mn, max_duration=mx)
    print(f"\nSelected {len(scenes)} scenes:")
    for sc in scenes:
        print(f"  {sc.start_time:.1f}s – {sc.end_time:.1f}s | score={sc.virality_score} | {sc.transcript[:80]}")
