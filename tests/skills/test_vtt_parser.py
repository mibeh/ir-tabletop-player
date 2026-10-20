from __future__ import annotations

from pathlib import Path

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_parses_voice_tag_and_colon_speakers(vtt_parser):
    cues = vtt_parser.parse_vtt((_FIXTURES / "sample.vtt").read_text())
    assert len(cues) == 3
    assert cues[0].speaker == "Alex Chen"
    assert "suspicious inbox rule" in cues[0].text
    assert cues[1].speaker == "Jordan Lee"
    assert "revoke the M365 sessions" in cues[1].text


def test_parses_timestamps_to_seconds(vtt_parser):
    cues = vtt_parser.parse_vtt((_FIXTURES / "sample.vtt").read_text())
    assert cues[0].start == 1.0
    assert cues[0].end == 5.0
    assert cues[2].start == 60.0


def test_skips_note_and_blank_and_malformed(vtt_parser):
    text = "WEBVTT\n\nNOTE ignore me\n\ngarbage line without arrow\n\n00:00:02.000 --> 00:00:03.000\nHello there\n"
    cues = vtt_parser.parse_vtt(text)
    assert len(cues) == 1
    assert cues[0].speaker is None
    assert cues[0].text == "Hello there"


def test_empty_input_returns_empty_list(vtt_parser):
    assert vtt_parser.parse_vtt("WEBVTT\n\n") == []


def test_parses_hh_mm_ss_timestamp(vtt_parser):
    text = "WEBVTT\n\n01:00:30.000 --> 01:00:31.000\nHello\n"
    cues = vtt_parser.parse_vtt(text)
    assert len(cues) == 1
    assert cues[0].start == 3630.0


def test_multiline_cue_body_is_space_joined(vtt_parser):
    text = "WEBVTT\n\n00:00:02.000 --> 00:00:03.000\nfirst line\nsecond line\n"
    cues = vtt_parser.parse_vtt(text)
    assert len(cues) == 1
    assert cues[0].text == "first line second line"


def test_parses_voice_tag_with_class_annotations(vtt_parser):
    text = "WEBVTT\n\n00:00:02.000 --> 00:00:03.000\n<v.loud.warning Alex Chen>Heads up\n"
    cues = vtt_parser.parse_vtt(text)
    assert len(cues) == 1
    assert cues[0].speaker == "Alex Chen"
    assert cues[0].text == "Heads up"


def test_colon_heuristic_false_positive_is_documented_behavior(vtt_parser):
    text = "WEBVTT\n\n00:00:02.000 --> 00:00:03.000\nThe solution: revoke sessions\n"
    cues = vtt_parser.parse_vtt(text)
    assert len(cues) == 1
    assert cues[0].speaker == "The solution"
    assert cues[0].text == "revoke sessions"
