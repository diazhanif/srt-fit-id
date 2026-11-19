"""Validate and reflow plain-text SRT captions without changing timestamps."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import Iterable


_CUE_INDEX = re.compile(r"[0-9]+\Z")
_TIMECODE = re.compile(
    r"^(?P<start>[0-9]{2,}:[0-5][0-9]:[0-5][0-9][,.][0-9]{3})"
    r"\s+-->\s+"
    r"(?P<end>[0-9]{2,}:[0-5][0-9]:[0-5][0-9][,.][0-9]{3})"
    r"(?P<settings>\s+.*)?$"
)


@dataclass(frozen=True)
class Cue:
    index: str
    timecode: str
    text: str


def _milliseconds(timestamp: str) -> int:
    normalized = timestamp.replace(",", ".")
    hours, minutes, seconds = normalized.split(":")
    whole_seconds, milliseconds = seconds.split(".")
    return (
        ((int(hours) * 60 + int(minutes)) * 60 + int(whole_seconds)) * 1000
        + int(milliseconds)
    )


def wrap_caption(text: str, max_chars: int = 42, max_lines: int = 2, cue_index: str = "?") -> list[str]:
    """Wrap one caption at word boundaries, raising instead of silently overflowing."""
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars < 1:
        raise ValueError("max_chars harus integer positif")
    if isinstance(max_lines, bool) or not isinstance(max_lines, int) or max_lines < 1:
        raise ValueError("max_lines harus integer positif")
    words = text.split()
    if not words:
        raise ValueError(f"cue {cue_index} tidak memiliki teks")
    if any(len(word) > max_chars for word in words):
        raise ValueError(f"cue {cue_index} memiliki kata yang lebih panjang dari batas {max_chars} karakter")

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        raise ValueError(
            f"cue {cue_index} memerlukan {len(lines)} baris; batas saat ini {max_lines} x {max_chars} karakter"
        )
    return lines


def parse_srt(content: str) -> list[Cue]:
    """Parse standard numbered SRT blocks and validate their time ranges."""
    if not isinstance(content, str):
        raise TypeError("konten SRT harus berupa string")
    normalized = content.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    blocks = re.split(r"\n[ \t]*\n+", normalized)
    cues: list[Cue] = []
    seen_indexes: set[str] = set()
    for block_number, block in enumerate(blocks, start=1):
        lines = block.split("\n")
        if len(lines) < 3 or not _CUE_INDEX.fullmatch(lines[0].strip()):
            raise ValueError(f"blok SRT {block_number} harus memiliki nomor, timestamp, dan teks")
        index = lines[0].strip()
        if index in seen_indexes:
            raise ValueError(f"nomor cue {index} duplikat")
        seen_indexes.add(index)
        timecode = lines[1].strip()
        match = _TIMECODE.fullmatch(timecode)
        if match is None:
            raise ValueError(f"timestamp pada cue {index} tidak valid")
        start_ms = _milliseconds(match.group("start"))
        end_ms = _milliseconds(match.group("end"))
        if end_ms <= start_ms:
            raise ValueError(f"waktu akhir cue {index} harus setelah waktu mulai")
        text = "\n".join(lines[2:]).strip()
        if not text:
            raise ValueError(f"cue {index} tidak memiliki teks")
        cues.append(Cue(index=index, timecode=timecode, text=text))
    return cues


def reflow_srt(content: str, max_chars: int = 42, max_lines: int = 2) -> str:
    """Return SRT with caption text rewrapped; cue indices/timings are unchanged."""
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars < 1:
        raise ValueError("max_chars harus integer positif")
    if isinstance(max_lines, bool) or not isinstance(max_lines, int) or max_lines < 1:
        raise ValueError("max_lines harus integer positif")
    cues = parse_srt(content)
    blocks = []
    for cue in cues:
        lines = wrap_caption(cue.text, max_chars=max_chars, max_lines=max_lines, cue_index=cue.index)
        blocks.append(f"{cue.index}\n{cue.timecode}\n" + "\n".join(lines))
    return "\n\n".join(blocks)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="srt-fit-id",
        description="Rapikan panjang baris subtitle SRT tanpa mengubah timestamp.",
    )
    parser.add_argument("--max-chars", type=int, default=42, help="maksimum karakter per baris (default: 42)")
    parser.add_argument("--max-lines", type=int, default=2, help="maksimum baris per cue (default: 2)")
    args = parser.parse_args(argv)
    try:
        result = reflow_srt(sys.stdin.read(), max_chars=args.max_chars, max_lines=args.max_lines)
    except (TypeError, ValueError) as error:
        print(f"srt-fit-id: {error}.", file=sys.stderr)
        return 2
    if result:
        sys.stdout.write(result + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
