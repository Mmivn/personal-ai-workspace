"""A small, self-drawn line-icon set — inline SVG, no external font or

icon library. This exists because relying on "fancy" Unicode symbol
blocks (astrological glyphs, dingbats) for the UI's iconography turned
out to be unreliable: on systems whose fonts don't cover that block,
those characters render as an empty "tofu" box instead of a symbol —
exactly the "empty square" the app was showing.

Every icon here is built from plain SVG primitives (circle/line/rect/
polygon) so it renders identically everywhere, with no font dependency
at all. Color comes from `currentColor`, so wrap usage in an element
with a `color` CSS rule (see .feature-icon / .panel-icon / .reading-icon
in ui/styles.py) to theme it.
"""

_WRAP_OPEN = (
    '<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
)
_WRAP_CLOSE = "</svg>"


def _icon(inner):
    def render(size=22):
        return _WRAP_OPEN.format(size=size) + inner + _WRAP_CLOSE

    return render


# Today — sunrise/sun.
sun = _icon(
    '<circle cx="12" cy="12" r="4.2"/>'
    '<line x1="12" y1="2.5" x2="12" y2="5"/>'
    '<line x1="12" y1="19" x2="12" y2="21.5"/>'
    '<line x1="2.5" y1="12" x2="5" y2="12"/>'
    '<line x1="19" y1="12" x2="21.5" y2="12"/>'
    '<line x1="5.2" y1="5.2" x2="7" y2="7"/>'
    '<line x1="17" y1="17" x2="18.8" y2="18.8"/>'
    '<line x1="5.2" y1="18.8" x2="7" y2="17"/>'
    '<line x1="17" y1="7" x2="18.8" y2="5.2"/>'
)

# This month — crescent moon.
moon = _icon('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>')

# This year — five-point star.
star = _icon(
    '<polygon points="12,2.5 14.9,9.3 22.2,9.9 16.6,14.6 18.3,21.8 '
    '12,17.8 5.7,21.8 7.4,14.6 1.8,9.9 9.1,9.3"/>'
)

# Compatibility — two overlapping circles.
venn = _icon('<circle cx="9" cy="12" r="6.3"/><circle cx="15" cy="12" r="6.3"/>')

# Ask AI — chat bubble with a typing indicator.
chat = _icon(
    '<path d="M4 5h16a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H9l-4 4v-4H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/>'
    '<circle cx="9" cy="10.4" r="0.65" fill="currentColor" stroke="none"/>'
    '<circle cx="12" cy="10.4" r="0.65" fill="currentColor" stroke="none"/>'
    '<circle cx="15" cy="10.4" r="0.65" fill="currentColor" stroke="none"/>'
)

# My sign / Life Path — a faceted gem.
gem = _icon(
    '<polygon points="12,3 19,9 12,21 5,9"/>'
    '<line x1="5" y1="9" x2="19" y2="9"/>'
    '<line x1="8.5" y1="9" x2="12" y2="3"/>'
    '<line x1="15.5" y1="9" x2="12" y2="3"/>'
)

# Full reading — a page with text lines.
scroll = _icon(
    '<rect x="5" y="3.5" width="14" height="17" rx="1.5"/>'
    '<line x1="8" y1="8" x2="16" y2="8"/>'
    '<line x1="8" y1="12" x2="16" y2="12"/>'
    '<line x1="8" y1="16" x2="13" y2="16"/>'
)

# A tiny sparkle accent used near the hero sign name / lead callouts.
spark = _icon(
    '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M18 6l-2.5 2.5M8.5 15.5L6 18"/>'
)


def hero_constellation(size=200):
    """A small decorative constellation — dots connected by faint lines,

    purely geometric so it renders identically everywhere.
    """
    points = [
        (30, 40), (70, 20), (150, 30), (175, 70),
        (150, 150), (60, 165), (25, 110),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0), (1, 6)]
    lines = "".join(
        f'<line x1="{points[a][0]}" y1="{points[a][1]}" '
        f'x2="{points[b][0]}" y2="{points[b][1]}" '
        'stroke="currentColor" stroke-width="0.6" stroke-opacity="0.35"/>'
        for a, b in edges
    )
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="{1.6 if i % 2 else 2.4}" '
        'fill="currentColor" fill-opacity="0.7"/>'
        for i, (x, y) in enumerate(points)
    )
    return (
        f'<svg viewBox="0 0 200 200" width="{size}" height="{size}" '
        'aria-hidden="true">' + lines + dots + "</svg>"
    )
