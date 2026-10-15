"""Render the comprehension map: one cell per unit, lit by human understanding."""
from .report import LIT, DRIFT


def render(report, cols=44, cell=14, gap=3):
    rows = sorted(report.rows, key=lambda r: (r.unit.path, r.unit.start))
    n = max(len(rows), 1)
    nrows = (n + cols - 1) // cols
    w = cols * (cell + gap) + 80
    h = nrows * (cell + gap) + 150
    lit, drift = len(report.by_state(LIT)), len(report.by_state(DRIFT))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
         '<defs><filter id="g"><feGaussianBlur stdDeviation="2.2" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<rect width="{w}" height="{h}" fill="#05060a"/>',
         '<text x="40" y="52" fill="#f5c542" font-family="Georgia,serif" font-size="26" letter-spacing="6">'
         'NOUS · COMPREHENSION MAP</text>',
         f'<text x="40" y="82" fill="#8aa0c8" font-family="monospace" font-size="14">'
         f'{report.coverage*100:.1f}% of code understood by a human · {lit} lit · {drift} drifted · '
         f'{len(rows) - lit - drift} dark</text>']
    for i, r in enumerate(rows):
        x, y = 40 + (i % cols) * (cell + gap), 110 + (i // cols) * (cell + gap)
        if r.state == LIT:
            o.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="#f5c542" filter="url(#g)"/>')
        elif r.state == DRIFT:
            o.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="#2a0f0f" stroke="#ff5a36" stroke-width="1.6"/>')
        else:
            o.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="#141a28"/>')
    o.append("</svg>")
    return "\n".join(o)
