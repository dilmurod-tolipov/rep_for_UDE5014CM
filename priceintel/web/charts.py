"""Inline SVG charts, written by hand so the dashboard needs no plotting library.

Why no matplotlib or plotly: the project must run from a clean checkout with nothing but the pinned
dependencies, and the dashboard is read by a browser, where SVG is the native format. Each function
returns a string of SVG that is embedded directly in the page, so there are no image files, no
temporary directories and nothing to serve.

Shared conventions:

* every chart has a ``<title>`` and axis labels, because an unlabelled chart is not evidence;
* values are drawn from the data as given - no smoothing, no clipping, no silent rescaling;
* colours come from CSS variables defined in ``views.py``, so light and dark mode both work and the
  bars keep enough contrast against the background;
* a chart with no data returns a short "no data" box rather than empty axes, so an empty category is
  visibly empty instead of looking broken.
"""
from html import escape

PALETTE = ("var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)")


def _no_data(width: int, height: int, message: str = "no data for this selection") -> str:
    return (f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">'
            f'<title>{escape(message)}</title>'
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="var(--panel)"/>'
            f'<text x="{width // 2}" y="{height // 2}" text-anchor="middle" '
            f'class="muted-text">{escape(message)}</text></svg>')


def _fmt(value: float) -> str:
    """Thousands separators, and millions as '1.2M' so axis labels stay short."""
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.0f}k"
    return f"{value:,.1f}".rstrip("0").rstrip(".")


def bar_chart(labels: list[str], values: list[float], *, title: str, value_label: str,
              width: int = 680, bar_height: int = 26, diverging: bool = False) -> str:
    """Horizontal bars, left to right. With ``diverging`` the axis is zero-centred, so negative
    values grow to the left of a zero line - used for "Secret is X% above/below" charts."""
    if not values:
        return _no_data(width, 120)
    label_w, pad, gap = 190, 70, 6
    plot_w = width - label_w - pad
    height = len(values) * (bar_height + gap) + 46
    top = 30
    high = max(max(values), 0.0)
    low = min(min(values), 0.0)
    span = (high - low) if diverging else high
    span = span or 1.0
    zero_x = label_w + (-low / span * plot_w if diverging else 0)

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">',
             f'<title>{escape(title)}</title>',
             f'<text x="0" y="16" class="chart-title">{escape(title)}</text>']
    for i, (label, value) in enumerate(zip(labels, values)):
        y = top + i * (bar_height + gap)
        length = abs(value) / span * plot_w
        x = zero_x - length if value < 0 else zero_x
        colour = "var(--down)" if (diverging and value < 0) else (
            "var(--up)" if diverging else PALETTE[i % len(PALETTE)])
        parts.append(f'<text x="{label_w - 8}" y="{y + bar_height - 8}" text-anchor="end" '
                     f'class="tick">{escape(label)}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{max(length, 1):.1f}" height="{bar_height}" '
                     f'fill="{colour}" rx="3"><title>{escape(label)}: {_fmt(value)} '
                     f'{escape(value_label)}</title></rect>')
        text_x = x + length + 6 if value >= 0 else x - 6
        anchor = "start" if value >= 0 else "end"
        parts.append(f'<text x="{text_x:.1f}" y="{y + bar_height - 8}" text-anchor="{anchor}" '
                     f'class="tick">{_fmt(value)}</text>')
    if diverging:
        parts.append(f'<line x1="{zero_x:.1f}" y1="{top - 4}" x2="{zero_x:.1f}" '
                     f'y2="{height - 20}" class="axis"/>')
    parts.append(f'<text x="{width - 4}" y="{height - 4}" text-anchor="end" class="axis-label">'
                 f'{escape(value_label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def grouped_bars(categories: list[str], series: dict[str, list[float]], *, title: str,
                 value_label: str, width: int = 680, height: int = 300) -> str:
    """Vertical bars grouped by category, one colour per series (one operator group)."""
    if not categories or not series:
        return _no_data(width, 160)
    left, right, top, bottom = 56, 12, 34, 64
    plot_w, plot_h = width - left - right, height - top - bottom
    peak = max((v for values in series.values() for v in values), default=0.0) or 1.0
    group_w = plot_w / len(categories)
    bar_w = max(group_w / (len(series) + 0.6), 3)

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">',
             f'<title>{escape(title)}</title>',
             f'<text x="0" y="16" class="chart-title">{escape(title)}</text>']
    for step in range(5):                                    # horizontal grid and y ticks
        value = peak * step / 4
        y = top + plot_h - plot_h * step / 4
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
                     f'class="grid"/>')
        parts.append(f'<text x="{left - 6}" y="{y + 4:.1f}" text-anchor="end" class="tick">'
                     f'{_fmt(value)}</text>')
    for ci, category in enumerate(categories):
        base = left + ci * group_w
        for si, (name, values) in enumerate(series.items()):
            value = values[ci] if ci < len(values) else 0.0
            bar_h = value / peak * plot_h
            x = base + si * bar_w + (group_w - bar_w * len(series)) / 2
            parts.append(f'<rect x="{x:.1f}" y="{top + plot_h - bar_h:.1f}" width="{bar_w:.1f}" '
                         f'height="{max(bar_h, 0.5):.1f}" fill="{PALETTE[si % len(PALETTE)]}" '
                         f'rx="2"><title>{escape(name)} - {escape(category)}: {_fmt(value)} '
                         f'{escape(value_label)}</title></rect>')
        parts.append(f'<text x="{base + group_w / 2:.1f}" y="{top + plot_h + 14}" '
                     f'text-anchor="middle" class="tick">{escape(category[:16])}</text>')
    for si, name in enumerate(series):
        x = left + si * 150
        parts.append(f'<rect x="{x}" y="{height - 26}" width="10" height="10" '
                     f'fill="{PALETTE[si % len(PALETTE)]}" rx="2"/>')
        parts.append(f'<text x="{x + 15}" y="{height - 17}" class="tick">{escape(name)}</text>')
    parts.append(f'<text x="4" y="{top - 8}" class="axis-label">{escape(value_label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def line_chart(labels: list[str], series: dict[str, list[float]], *, title: str, value_label: str,
               width: int = 680, height: int = 260) -> str:
    """One line per series over ordered labels (used for days of collection)."""
    if not labels or not series:
        return _no_data(width, 160)
    left, right, top, bottom = 56, 12, 34, 54
    plot_w, plot_h = width - left - right, height - top - bottom
    peak = max((v for values in series.values() for v in values), default=0.0) or 1.0
    step = plot_w / max(len(labels) - 1, 1)

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">',
             f'<title>{escape(title)}</title>',
             f'<text x="0" y="16" class="chart-title">{escape(title)}</text>']
    for tick in range(5):
        value = peak * tick / 4
        y = top + plot_h - plot_h * tick / 4
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left - 6}" y="{y + 4:.1f}" text-anchor="end" class="tick">'
                     f'{_fmt(value)}</text>')
    for si, (name, values) in enumerate(series.items()):
        points = " ".join(f"{left + i * step:.1f},{top + plot_h - (v / peak * plot_h):.1f}"
                          for i, v in enumerate(values))
        colour = PALETTE[si % len(PALETTE)]
        parts.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="2"/>')
        for i, v in enumerate(values):
            parts.append(f'<circle cx="{left + i * step:.1f}" '
                         f'cy="{top + plot_h - (v / peak * plot_h):.1f}" r="3" fill="{colour}">'
                         f'<title>{escape(name)} {escape(labels[i])}: {_fmt(v)} '
                         f'{escape(value_label)}</title></circle>')
        parts.append(f'<rect x="{left + si * 150}" y="{height - 22}" width="10" height="10" '
                     f'fill="{colour}" rx="2"/>')
        parts.append(f'<text x="{left + si * 150 + 15}" y="{height - 13}" class="tick">'
                     f'{escape(name)}</text>')
    for i, label in enumerate(labels):
        if len(labels) <= 10 or i % max(len(labels) // 8, 1) == 0:
            parts.append(f'<text x="{left + i * step:.1f}" y="{top + plot_h + 16}" '
                         f'text-anchor="middle" class="tick">{escape(label[5:])}</text>')
    parts.append(f'<text x="4" y="{top - 8}" class="axis-label">{escape(value_label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def histogram(values: list[float], *, title: str, value_label: str, bins: int = 18,
              width: int = 680, height: int = 260) -> str:
    """Distribution of one list of numbers. Bin edges are linear between the minimum and maximum,
    which keeps the shape honest: no log axis unless the page says so."""
    if not values:
        return _no_data(width, 160)
    low, high = min(values), max(values)
    if high == low:
        high = low + 1
    edge = (high - low) / bins
    counts = [0] * bins
    for v in values:
        counts[min(int((v - low) / edge), bins - 1)] += 1

    left, right, top, bottom = 48, 12, 34, 52
    plot_w, plot_h = width - left - right, height - top - bottom
    peak = max(counts) or 1
    bar_w = plot_w / bins
    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">',
             f'<title>{escape(title)}</title>',
             f'<text x="0" y="16" class="chart-title">{escape(title)}</text>']
    for i, count in enumerate(counts):
        bar_h = count / peak * plot_h
        parts.append(f'<rect x="{left + i * bar_w:.1f}" y="{top + plot_h - bar_h:.1f}" '
                     f'width="{bar_w - 1.5:.1f}" height="{max(bar_h, 0.5):.1f}" fill="var(--c1)" '
                     f'rx="2"><title>{_fmt(low + i * edge)} to {_fmt(low + (i + 1) * edge)}: '
                     f'{count} products</title></rect>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" '
                 f'y2="{top + plot_h}" class="axis"/>')
    for i in (0, bins // 2, bins):
        parts.append(f'<text x="{left + i * bar_w:.1f}" y="{top + plot_h + 16}" '
                     f'text-anchor="middle" class="tick">{_fmt(low + i * edge)}</text>')
    parts.append(f'<text x="{left}" y="{top - 8}" class="axis-label">products</text>')
    parts.append(f'<text x="{width - 4}" y="{height - 6}" text-anchor="end" class="axis-label">'
                 f'{escape(value_label)}</text>')
    parts.append("</svg>")
    return "".join(parts)
