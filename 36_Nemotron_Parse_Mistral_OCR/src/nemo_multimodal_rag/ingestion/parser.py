"""Phase 1: Parse raw nemotron-parse JSON results into structured elements."""

from __future__ import annotations

import dataclasses
import json
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Element types to discard entirely
_SKIP_TYPES = {"Page-footer"}

# Marker used by nemotron-parse to indicate truncated / continued content
_TBC = "<tbc>"


@dataclasses.dataclass
class ParsedElement:
    """One semantic element extracted from a single PDF page."""

    page_num: int
    element_index: int
    element_type: str
    text: str
    bbox: dict  # {"xmin": float, "ymin": float, "xmax": float, "ymax": float}
    is_tbc: bool  # True if text ends with <tbc> (continues on next element)


def _page_num_from_path(path: Path) -> int:
    """Extract 0-indexed page number from filename like docling_report_page_0003_raw.json."""
    match = re.search(r"page_(\d{4})_raw", path.name)
    if not match:
        raise ValueError(f"Cannot parse page number from filename: {path.name}")
    return int(match.group(1))


def _parse_single_file(path: Path) -> list[ParsedElement]:
    """Load one *_raw.json file and return its ParsedElement list."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    page_num = _page_num_from_path(path)

    try:
        arguments_str: str = (
            raw["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
        )
    except (KeyError, IndexError, TypeError) as exc:
        log.warning("Skipping %s — cannot locate tool_calls: %s", path.name, exc)
        return []

    # The arguments field is a JSON-encoded string; parse it
    try:
        outer = json.loads(arguments_str)
    except json.JSONDecodeError as exc:
        log.warning("Skipping %s — JSON decode error: %s", path.name, exc)
        return []

    # nemotron-parse wraps the element list in an extra array: [[{...}, ...]]
    if isinstance(outer, list) and outer and isinstance(outer[0], list):
        element_dicts = outer[0]
    elif isinstance(outer, list):
        element_dicts = outer
    else:
        log.warning("Unexpected arguments structure in %s — skipping", path.name)
        return []

    elements: list[ParsedElement] = []
    for idx, item in enumerate(element_dicts):
        if not isinstance(item, dict):
            continue
        elem_type = item.get("type", "Text")
        if elem_type in _SKIP_TYPES:
            continue
        text: str = item.get("text", "") or ""
        bbox: dict = item.get("bbox", {"xmin": 0.0, "ymin": 0.0, "xmax": 1.0, "ymax": 1.0})
        is_tbc = text.rstrip().endswith(_TBC)
        elements.append(
            ParsedElement(
                page_num=page_num,
                element_index=idx,
                element_type=elem_type,
                text=text,
                bbox=bbox,
                is_tbc=is_tbc,
            )
        )

    return elements


def parse_raw_results(results_dir: Path) -> list[ParsedElement]:
    """Load all *_raw.json files and return elements sorted by (page_num, element_index).

    Args:
        results_dir: Directory containing the nemotron-parse output JSON files.

    Returns:
        Flat list of ParsedElement objects across all pages, in reading order.
    """
    raw_files = sorted(results_dir.glob("*_raw.json"))
    if not raw_files:
        raise FileNotFoundError(f"No *_raw.json files found in {results_dir}")

    all_elements: list[ParsedElement] = []
    for path in raw_files:
        elements = _parse_single_file(path)
        all_elements.extend(elements)
        log.debug("Parsed %d elements from %s", len(elements), path.name)

    all_elements.sort(key=lambda e: (e.page_num, e.element_index))
    log.info("Parsed %d elements across %d pages", len(all_elements), len(raw_files))
    return all_elements


def stitch_continuations(elements: list[ParsedElement]) -> list[ParsedElement]:
    """Merge <tbc>-terminated elements with their following sibling.

    When nemotron-parse hits the token limit mid-element it appends ``<tbc>``
    and the next element (possibly on the next page) starts with ``<tbc>`` as
    a signal that it is the continuation.  This function splices them together
    so downstream chunking sees complete text.

    Args:
        elements: Flat list of elements in reading order.

    Returns:
        New list with continuation pairs merged into single elements.
    """
    result: list[ParsedElement] = []
    i = 0

    while i < len(elements):
        elem = elements[i]

        if elem.is_tbc:
            # Strip trailing <tbc> marker
            combined_text = elem.text.rstrip()
            if combined_text.endswith(_TBC):
                combined_text = combined_text[: -len(_TBC)].rstrip()

            i += 1
            while i < len(elements):
                nxt = elements[i]
                nxt_text = nxt.text
                if nxt_text.startswith(_TBC):
                    continuation = nxt_text[len(_TBC) :].lstrip()
                    combined_text = combined_text + " " + continuation
                    i += 1
                    # If the continuation is itself tbc, keep going
                    if continuation.rstrip().endswith(_TBC):
                        combined_text = combined_text.rstrip()[: -len(_TBC)].rstrip()
                    else:
                        break
                else:
                    # Next element is NOT a continuation — stop merging
                    break

            merged = dataclasses.replace(elem, text=combined_text, is_tbc=False)
            result.append(merged)

        elif elem.text.startswith(_TBC):
            # Orphaned continuation (its predecessor was already processed or
            # from a previous session without stitching) — strip the marker.
            clean_text = elem.text[len(_TBC) :].lstrip()
            result.append(dataclasses.replace(elem, text=clean_text, is_tbc=False))
            i += 1

        else:
            result.append(elem)
            i += 1

    log.info(
        "Stitched continuations: %d elements → %d elements",
        len(elements),
        len(result),
    )
    return result
