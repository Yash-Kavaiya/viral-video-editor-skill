"""
viral_scorer.py

Scores each video segment for viral potential using:
- Cosine similarity to reference viral embedding patterns
- Heuristic scoring on speech rate, emotion, and position
"""

import numpy as np
from scipy.spatial.distance import cosine
from dataclasses import dataclass
from typing import Optional

from video_analyzer import SceneSegment, VideoAnalysis


# Reference "viral" embedding prototype (seeded from known high-engagement patterns)
# In production, replace with real embeddings from actual viral videos
VIRAL_EMOTION_SCORES = {
    "excitement": 1.0,
    "surprise": 0.9,
    "joy": 0.8,
    "anger": 0.7,   # controversy can go viral
    "neutral": 0.4,
    "sad": 0.5,
}

OPTIMAL_WPM_MIN = 120
OPTIMAL_WPM_MAX = 170


@dataclass
class ScoredSegment:
    segment: SceneSegment
    hook_score: float       # 0-1: Is this a strong opening hook?
    emotion_score: float    # 0-1: Emotional intensity
    pacing_score: float     # 0-1: Speech rate in viral sweet spot
    position_score: float   # 0-1: Penalty for mid-sentence cuts
    embedding_score: float  # 0-1: Similarity to viral patterns
    total_score: float      # Weighted combination


class ViralScorer:
    """
    Scores segments and selects the best ones for a viral reel.
    """

    WEIGHTS = {
        "hook": 0.25,
        "emotion": 0.25,
        "pacing": 0.20,
        "position": 0.15,
        "embedding": 0.15,
    }

    HOOK_PHRASES = [
        "did you know", "the truth about", "nobody talks about",
        "i was wrong", "you won't believe", "stop doing",
        "the reason why", "what if i told you", "secret",
        "mistake", "change your life", "most people", "actually",
    ]

    def __init__(self, reference_embeddings: Optional[list[list[float]]] = None):
        """
        Args:
            reference_embeddings: List of embedding vectors from known viral videos.
                                  If None, embedding scoring is skipped.
        """
        self.reference_embeddings = reference_embeddings

    def score_analysis(self, analysis: VideoAnalysis) -> list[ScoredSegment]:
        """Score all segments in a VideoAnalysis and sort by total_score descending."""
        scored = [self._score_segment(seg, analysis) for seg in analysis.segments]
        scored.sort(key=lambda s: s.total_score, reverse=True)
        return scored

    def select_segments_for_reel(
        self,
        scored: list[ScoredSegment],
        min_duration: float = 45.0,
        max_duration: float = 90.0,
    ) -> list[SceneSegment]:
        """
        Greedily select top-scored segments that fit within target duration.
        Returns segments in chronological order.
        """
        total_duration = 0.0
        selected = []

        for s in scored:
            seg_duration = s.segment.end_time - s.segment.start_time
            if total_duration + seg_duration <= max_duration:
                selected.append(s.segment)
                total_duration += seg_duration
            if total_duration >= min_duration:
                break

        # Sort chronologically for natural flow
        selected.sort(key=lambda seg: seg.start_time)
        return selected

    # ------------------------------------------------------------------
    # Private scoring methods
    # ------------------------------------------------------------------

    def _score_segment(self, seg: SceneSegment, analysis: VideoAnalysis) -> ScoredSegment:
        hook = self._score_hook(seg)
        emotion = self._score_emotion(seg)
        pacing = self._score_pacing(seg)
        position = self._score_position(seg, analysis)
        embedding = self._score_embedding(seg)

        total = (
            self.WEIGHTS["hook"] * hook
            + self.WEIGHTS["emotion"] * emotion
            + self.WEIGHTS["pacing"] * pacing
            + self.WEIGHTS["position"] * position
            + self.WEIGHTS["embedding"] * embedding
        )

        seg.virality_score = round(total * 100, 1)

        return ScoredSegment(
            segment=seg,
            hook_score=hook,
            emotion_score=emotion,
            pacing_score=pacing,
            position_score=position,
            embedding_score=embedding,
            total_score=total,
        )

    def _score_hook(self, seg: SceneSegment) -> float:
        """Check if the transcript contains viral hook language."""
        text_lower = seg.transcript.lower()
        matches = sum(1 for phrase in self.HOOK_PHRASES if phrase in text_lower)
        return min(matches * 0.3, 1.0)

    def _score_emotion(self, seg: SceneSegment) -> float:
        return VIRAL_EMOTION_SCORES.get(seg.emotional_tone, 0.4)

    def _score_pacing(self, seg: SceneSegment) -> float:
        wpm = seg.speech_rate_wpm
        if OPTIMAL_WPM_MIN <= wpm <= OPTIMAL_WPM_MAX:
            return 1.0
        elif wpm < OPTIMAL_WPM_MIN:
            return max(0, wpm / OPTIMAL_WPM_MIN)
        else:  # too fast
            return max(0, 1 - (wpm - OPTIMAL_WPM_MAX) / 100)

    def _score_position(self, seg: SceneSegment, analysis: VideoAnalysis) -> float:
        """Favor segments that start at a sentence boundary (non-zero score only)."""
        text = seg.transcript.strip()
        # Penalize if transcript starts with a lowercase connector word
        connectors = ["and ", "but ", "so ", "the ", "a ", "that ", "which ", "or "]
        if any(text.lower().startswith(c) for c in connectors):
            return 0.3
        return 1.0

    def _score_embedding(self, seg: SceneSegment) -> float:
        """Cosine similarity of segment embedding to reference viral embeddings."""
        if not self.reference_embeddings or not seg.embedding or all(v == 0 for v in seg.embedding):
            return 0.5  # neutral score when no reference available

        seg_vec = np.array(seg.embedding)
        similarities = [
            1 - cosine(seg_vec, np.array(ref))
            for ref in self.reference_embeddings
            if len(ref) == len(seg.embedding)
        ]
        return float(np.mean(similarities)) if similarities else 0.5
