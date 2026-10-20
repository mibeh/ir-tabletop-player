"""Parse WebVTT (.vtt) transcripts into speaker turns.

Supports Microsoft Teams voice tags (``<v Speaker>text</v>``) and Zoom-style
``Speaker: text`` prefixes. Header, NOTE blocks, and malformed cues are skipped.

The Zoom colon heuristic is best-effort: a cue beginning with a noun phrase
followed by ``": "`` may be misread as a speaker label. This is an accepted
tradeoff for Zoom VTT, which carries no structured speaker tag.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_TS = r"(?:\d{1,2}:)?\d{1,2}:\d{2}\.\d{3}"
_TIMING_RE = re.compile(rf"^\s*({_TS})\s*-->\s*({_TS})")
_VOICE_RE = re.compile(
    r"<v(?:\.[^\s>.]+)*\s+([\w][\w .,'\-]*?)\s*>(.*?)(?:</v>)?\s*$",
    re.IGNORECASE | re.DOTALL,
)
_COLON_RE = re.compile(r"^([A-Za-z][\w .,'\-]{0,60}):\s+(.*)$", re.DOTALL)


@dataclass
class Cue:
    """One transcript turn: timing in seconds, optional speaker, spoken text."""

    start: float
    end: float
    speaker: str | None
    text: str


def _to_seconds(stamp: str) -> float:
    """Convert a ``[HH:]MM:SS.mmm`` WebVTT timestamp to seconds."""
    parts = stamp.split(":")
    parts = ["0", *parts] if len(parts) == 2 else parts
    hours, minutes, rest = parts
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def _split_speaker(body: str) -> tuple[str | None, str]:
    """Split a cue body into ``(speaker, text)`` using voice-tag or colon prefix.

    The Zoom-style ``Speaker: text`` heuristic may misclassify cue text that
    begins with a noun phrase followed by ``": "`` (e.g. ``"The solution: ..."``
    yields speaker ``"The solution"``). This is an accepted tradeoff for Zoom
    VTT, which has no structured speaker tag to disambiguate.
    """
    voice = _VOICE_RE.match(body.strip())
    if voice:
        return voice.group(1).strip(), voice.group(2).strip()
    colon = _COLON_RE.match(body.strip())
    if colon:
        return colon.group(1).strip(), colon.group(2).strip()
    return None, body.strip()


def parse_vtt(text: str) -> list[Cue]:
    """Return the cues in a WebVTT document as a list of :class:`Cue`."""
    cues: list[Cue] = []
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip()]
        if not lines or lines[0].strip().startswith(("WEBVTT", "NOTE")):
            continue
        timing_idx = next(
            (i for i, ln in enumerate(lines) if _TIMING_RE.match(ln)), None
        )
        if timing_idx is None:
            continue
        match = _TIMING_RE.match(lines[timing_idx])
        body = " ".join(lines[timing_idx + 1 :]).strip()
        if not body:
            continue
        speaker, spoken = _split_speaker(body)
        cues.append(
            Cue(
                start=_to_seconds(match.group(1)),
                end=_to_seconds(match.group(2)),
                speaker=speaker,
                text=spoken,
            )
        )
    return cues
