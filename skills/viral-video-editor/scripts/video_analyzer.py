"""
video_analyzer.py

Uses Gemini Embedding 2 to analyze video content and extract:
- Multimodal embeddings per scene segment
- Full transcript with timestamps
- Speaker diarization
- Visual/emotional energy per scene
"""

import os
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class SceneSegment:
    """Represents one analyzed scene segment of the video."""
    index: int
    start_time: float          # seconds
    end_time: float            # seconds
    embedding: list[float]     # Gemini Embedding 2 vector (768-dim)
    transcript: str            # What was said in this segment
    speaker_id: str            # Speaker label (SPEAKER_00, SPEAKER_01, ...)
    visual_description: str    # Gemini's description of visual content
    emotional_tone: str        # detected emotion: joy/surprise/neutral/sad/anger
    speech_rate_wpm: float     # estimated words per minute
    virality_score: float = 0.0  # filled in by viral_scorer.py


@dataclass
class VideoAnalysis:
    """Full analysis result for a video file."""
    video_path: str
    duration: float
    segments: list[SceneSegment] = field(default_factory=list)
    full_transcript: str = ""
    language: str = "en"
    metadata: dict = field(default_factory=dict)


class GeminiVideoAnalyzer:
    """
    Analyzes video files using Gemini Embedding 2 and Gemini Flash.

    Gemini Embedding 2 supports:
    - Video: up to 120 seconds, MP4/MOV, H264/H265/AV1/VP9
    - Processes max 32 frames (1fps for <=32s, uniform sampling for longer)
    """

    EMBEDDING_MODEL = "gemini-embedding-2"
    ANALYSIS_MODEL = "gemini-2.5-flash"   # For transcript / description
    SEGMENT_DURATION = 30.0               # Analyze in 30-second chunks
    MAX_EMBEDDING_DURATION = 120.0        # Gemini Embedding 2 limit

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ["GEMINI_API_KEY"]
        self.client = genai.Client(api_key=self.api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, video_path: str) -> VideoAnalysis:
        """Full analysis pipeline for a video file."""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        logger.info(f"Starting analysis of {video_path.name}")
        duration = self._get_video_duration(str(video_path))
        analysis = VideoAnalysis(video_path=str(video_path), duration=duration)

        # Step 1: Get full transcript + scene descriptions via Gemini Flash
        transcript_data = self._extract_transcript_and_scenes(str(video_path))
        analysis.full_transcript = transcript_data.get("full_transcript", "")
        analysis.language = transcript_data.get("language", "en")

        # Step 2: Generate embeddings per segment
        segments_data = transcript_data.get("segments", [])
        for i, seg in enumerate(segments_data):
            start = seg["start"]
            end = min(seg["end"], duration)
            segment_duration = end - start

            # Clip segment for embedding (max 120s)
            clip_end = min(end, start + self.MAX_EMBEDDING_DURATION)
            embedding = self._get_segment_embedding(str(video_path), start, clip_end)

            wpm = self._estimate_wpm(seg.get("text", ""), segment_duration)

            scene = SceneSegment(
                index=i,
                start_time=start,
                end_time=end,
                embedding=embedding,
                transcript=seg.get("text", ""),
                speaker_id=seg.get("speaker", "SPEAKER_00"),
                visual_description=seg.get("visual_description", ""),
                emotional_tone=seg.get("emotional_tone", "neutral"),
                speech_rate_wpm=wpm,
            )
            analysis.segments.append(scene)
            logger.info(f"  Segment {i+1}/{len(segments_data)} embedded ({start:.1f}s–{end:.1f}s)")

        logger.info(f"Analysis complete: {len(analysis.segments)} segments")
        return analysis

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_transcript_and_scenes(self, video_path: str) -> dict:
        """Use Gemini Flash to extract transcripts, scene descriptions, and emotions."""
        prompt = """Analyze this video and return a JSON object with the following structure:
{
  "language": "en",
  "full_transcript": "complete spoken text",
  "segments": [
    {
      "start": 0.0,
      "end": 30.0,
      "text": "text spoken in this segment",
      "speaker": "SPEAKER_00",
      "visual_description": "what is visually happening",
      "emotional_tone": "joy|surprise|neutral|sad|anger|excitement"
    }
  ]
}
Divide into 30-second segments. Be precise with timestamps.
Only return valid JSON, no markdown code blocks."""

        video_bytes = Path(video_path).read_bytes()
        response = self.client.models.generate_content(
            model=self.ANALYSIS_MODEL,
            contents=types.Content(
                parts=[
                    types.Part(inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")),
                    types.Part(text=prompt),
                ]
            ),
        )
        raw = response.text.strip()
        # Strip potential markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON transcript, returning empty")
            return {"full_transcript": raw, "segments": [], "language": "en"}

    def _get_segment_embedding(self, video_path: str, start: float, end: float) -> list[float]:
        """
        Extract a video segment and get its Gemini Embedding 2 embedding.
        For short videos (<= 120s total), embed the full video.
        For longer videos, embed the specific segment by reading bytes.
        """
        try:
            # Use FFmpeg to extract the segment to temp file
            import tempfile
            import subprocess

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name

            duration = end - start
            cmd = [
                "ffmpeg", "-ss", str(start), "-t", str(duration),
                "-i", video_path, "-c", "copy", "-y", tmp_path, "-loglevel", "quiet"
            ]
            subprocess.run(cmd, check=True, capture_output=True)

            video_bytes = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)

            result = self.client.models.embed_content(
                model=self.EMBEDDING_MODEL,
                contents=[
                    types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
                ],
            )
            return result.embeddings[0].values

        except Exception as e:
            logger.warning(f"Embedding failed for segment {start}-{end}: {e}")
            return [0.0] * 768  # Return zero vector on failure

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe."""
        import subprocess
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))

    @staticmethod
    def _estimate_wpm(text: str, duration_seconds: float) -> float:
        """Estimate words per minute from text and duration."""
        if duration_seconds <= 0:
            return 0
        word_count = len(text.split())
        return (word_count / duration_seconds) * 60
