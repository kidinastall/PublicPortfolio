"""Approved text, selected by ID. The model never phrases these."""
import json
from pathlib import Path

_LIB = Path(__file__).parent / "prompts" / "library"
_BLOCKS = json.loads((_LIB / "copy_blocks.json").read_text())["blocks"]
_HANDOFFS = json.loads((_LIB / "handoff_templates.json").read_text())


def block(block_id):
    return _BLOCKS[block_id]


def text(block_id):
    """Text for a copy block (DISC-, FB-, LM-, GR-, CF-, CL-) or a handoff template (HT-)."""
    return (_HANDOFFS[block_id] if block_id.startswith("HT-") else _BLOCKS[block_id])["text"]


def disclosure_banner():
    """Session-start AlertBanner so the user always knows they are talking to an AI."""
    b = _BLOCKS["DISC-001"]
    return {"type": "AlertBanner", "props": {"severity": "info", "title": b["title"], "body": b["body"]}}
