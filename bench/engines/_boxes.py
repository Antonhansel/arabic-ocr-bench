"""Turn word or line boxes into page text, for engines that return boxes but
no page-level reading order (PaddleOCR, Apple Vision).

Rule, applied the same way to every such engine: group boxes into lines when
their vertical spans overlap by at least half of the smaller box height,
order lines top to bottom, and boxes inside a line right to left (Arabic).
No column detection: a two-column page comes out row by row, which is what
a developer gets without a layout model.
"""
from __future__ import annotations


def rtl_lines(boxes: list[tuple[float, float, float, float, str]]) -> str:
    """boxes: (x0, y0, x1, y1, text) in pixels, y growing downwards."""
    lines: list[list[tuple]] = []
    for b in sorted(boxes, key=lambda b: (b[1] + b[3]) / 2):
        x0, y0, x1, y1, text = b
        if not text.strip():
            continue
        for line in lines:
            ly0 = min(t[1] for t in line)
            ly1 = max(t[3] for t in line)
            overlap = min(y1, ly1) - max(y0, ly0)
            if overlap >= 0.5 * min(y1 - y0, ly1 - ly0):
                line.append(b)
                break
        else:
            lines.append([b])
    lines.sort(key=lambda ln: sum((t[1] + t[3]) / 2 for t in ln) / len(ln))
    return "\n".join(
        " ".join(t[4].strip() for t in sorted(ln, key=lambda t: -(t[0] + t[2]) / 2))
        for ln in lines
    )
