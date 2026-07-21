"""Theme helpers for the web interface.

The notebook UI follows a 3-color, 60/30/10 rule:

  * ``base``    (60%) - page background
  * ``surface`` (30%) - cards, nav, sidebar, editor chrome
  * ``accent``  (10%) - buttons, links, highlights, focus

These three colors are user-configurable in ``.qmd_conf`` under a ``theme:``
section. All other colors the UI needs (text, muted text, borders, button
hover, editor selection, ...) are *derived* from those three so that any
palette -- light or dark -- stays readable without the user having to pick a
dozen colors themselves.
"""

DEFAULT_THEME = {
    "base": "#f4f5f7",
    "surface": "#ffffff",
    "accent": "#3498db",
}


def hex_to_rgb(h):
    h = str(h).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _channel(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
    r, g, b = rgb
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_text(hex_color, dark="#1b1f24", light="#f3f5f8"):
    """Return a readable text color (dark or light) for the given background."""
    return dark if relative_luminance(hex_to_rgb(hex_color)) > 0.42 else light


def mix(h1, h2, t):
    """Blend two hex colors; t=0 -> h1, t=1 -> h2."""
    a, b = hex_to_rgb(h1), hex_to_rgb(h2)
    return rgb_to_hex(tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3)))


def rgba(hex_color, alpha):
    r, g, b = hex_to_rgb(hex_color)
    return "rgba({},{},{},{})".format(r, g, b, alpha)


def _is_hex(v):
    return isinstance(v, str) and re_fullmatch(v)


def re_fullmatch(v):
    import re
    return re.fullmatch(r"#?[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?", v)


def resolve_theme(theme_cfg):
    """Given the raw ``theme`` dict from config, return a fully-resolved palette."""
    t = dict(DEFAULT_THEME)
    if isinstance(theme_cfg, dict):
        for k in ("base", "surface", "accent"):
            v = theme_cfg.get(k)
            if _is_hex(v):
                t[k] = v if v.startswith("#") else "#" + v
    text = contrast_text(t["surface"])
    text_on_accent = contrast_text(t["accent"])
    text_on_base = contrast_text(t["base"])
    return {
        # The three configured colors.
        "base": t["base"],
        "surface": t["surface"],
        "accent": t["accent"],
        # Derived: text readable on each.
        "text": text,
        "text_on_accent": text_on_accent,
        "text_on_base": text_on_base,
        # Derived: secondary text + borders on the surface.
        "muted": mix(text, t["surface"], 0.45),
        "border": mix(text, t["surface"], 0.86),
        # Derived: accent hover (blend toward its contrast text).
        "accent_hover": mix(t["accent"], text_on_accent, 0.18),
        # Derived: editor chrome.
        "active_line": mix(text, t["surface"], 0.93),
        "selection": rgba(t["accent"], 0.25),
        "gutter_text": mix(text, t["surface"], 0.5),
    }