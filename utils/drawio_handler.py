"""Helpers for draw.io ".drawio.svg" diagrams.

A ``.drawio.svg`` file is an ordinary SVG (so any browser can render it as an
image without exporting) that also carries the editable diagram source. draw.io
stores the source in a ``content`` attribute on the root ``<svg>`` element when
it exports with "Include a copy of my diagram" / the embed ``xmlsvg`` export
format. This is draw.io's *native* embedded format, so the files we write are
re-openable in the draw.io desktop app too.

The two operations we need:

* :func:`extract_embedded_xml` -- pull the diagram XML back out of a stored
  ``.drawio.svg`` so it can be reloaded into the embed editor.
* :func:`write_embedded_svg` -- persist an SVG that came back from the embed
  editor, making sure it actually carries its source so re-editing keeps
  working.
"""

import os
import re

try:
    import xml.etree.ElementTree as ET
except ImportError:  # pragma: no cover - stdlib always present
    ET = None


# Matches the root <svg ...> opening tag and a `content="..."` attribute on it.
# Attribute values escape embedded quotes as &quot;, so [^"]* is safe.
_SVG_OPEN_RE = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_CONTENT_ATTR_RE = re.compile(r'\bcontent="([^"]*)"', re.IGNORECASE)


def extract_embedded_xml(svg_text):
    """Return the embedded diagram XML from a ``.drawio.svg`` string.

    Returns ``None`` if no embedded source is found (e.g. a plain SVG with no
    diagram copy). The returned XML is what draw.io's embed ``load`` action
    accepts directly as ``data.xml``.
    """
    if not svg_text:
        return None

    # Preferred path: parse with ElementTree so XML-escaping in the attribute
    # value is handled for us.
    if ET is not None:
        try:
            # draw.io SVGs may have a leading XML declaration / DOCTYPE; ET
            # handles the declaration fine. Parse the whole document.
            root = ET.fromstring(svg_text)
            # ElementTree expands namespaces; the `content` attribute is
            # unqualified, so look it up directly.
            content = root.get("content")
            if content:
                return content
        except ET.ParseError:
            pass  # fall through to regex

    # Fallback: regex over the opening <svg> tag.
    open_tag = _SVG_OPEN_RE.search(svg_text)
    if open_tag:
        m = _CONTENT_ATTR_RE.search(open_tag.group(0))
        if m:
            # Un-escape the standard XML entities draw.io writes.
            return _xml_unescape(m.group(1))

    return None


def _xml_unescape(s):
    return (s.replace("&lt;", "<")
             .replace("&gt;", ">")
             .replace("&quot;", '"')
             .replace("&#10;", "\n")
             .replace("&#9;", "\t")
             .replace("&amp;", "&"))


def _xml_escape_attr(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("\n", "&#10;")
             .replace("\t", "&#9;"))


def _ensure_embedded(svg_text, fallback_xml):
    """Guarantee the SVG root carries a `content` attribute with its source.

    draw.io's ``xmlsvg`` export already embeds the source, so this is usually a
    no-op. If for some reason it doesn't (e.g. a plain SVG export slipped in),
    inject ``fallback_xml`` so the file stays re-editable.
    """
    if not svg_text or "<svg" not in svg_text.lower():
        raise ValueError("Supplied content is not a valid SVG document")

    open_tag = _SVG_OPEN_RE.search(svg_text)
    if open_tag and _CONTENT_ATTR_RE.search(open_tag.group(0)):
        return svg_text

    if not fallback_xml:
        return svg_text

    # Inject the content attribute into the root <svg ...> opening tag.
    open_match = _SVG_OPEN_RE.search(svg_text)
    if not open_match:
        return svg_text
    open_tag = open_match.group(0)
    injected = open_tag[:-1] + f' content="{_xml_escape_attr(fallback_xml)}">'
    return svg_text[:open_match.start()] + injected + svg_text[open_match.end():]


def write_embedded_svg(svg_text, dest_path, fallback_xml=None):
    """Persist a draw.io SVG to ``dest_path``.

    Validates that ``svg_text`` is an SVG and ensures it carries its embedded
    diagram source (injecting ``fallback_xml`` when the export didn't include
    it). Parent directories are created as needed.
    """
    if not svg_text or "<svg" not in svg_text.lower():
        raise ValueError("Supplied content is not a valid SVG document")

    final = _ensure_embedded(svg_text, fallback_xml)

    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(final)


def create_markdown_link(alt_text, relative_path):
    """Generate a markdown image link for a .drawio.svg diagram.

    Because .drawio.svg files are real SVGs, a normal markdown image link
    renders them inline in the rendered page.
    """
    return f"![{alt_text}]({relative_path})"