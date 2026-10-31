"""End-to-end endpoint tests for the quick-md web server.

Creates a temporary notebook directory with realistic structure,
boots a Flask test client, and exercises every route to verify
behaviour — especially media-path handling, page CRUD, uploads,
search, and the draw.io endpoints.

Run with:
    cd quick-md
    python -m pytest tests/ -v
"""

import io
import os
import re
import shutil
import tempfile

import pytest
import yaml

# ---------------------------------------------------------------------------
# Fixture: temporary notebook + Flask test client
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_client():
    """Yield a Flask test client backed by a throwaway notebook directory.

    The notebook has:
      - main.md              (index page with a couple of links)
      - images/              (directory with one real PNG)
      - videos/              (empty directory)
      - figures/             (empty directory)
      - .qmd_conf            (configuration pointing at the above)
    """
    tmp = tempfile.mkdtemp(prefix="qmd_test_")
    try:
        # --- Directories ---
        images_dir = os.path.join(tmp, "images")
        videos_dir = os.path.join(tmp, "videos")
        figures_dir = os.path.join(tmp, "figures")
        for d in (images_dir, videos_dir, figures_dir):
            os.makedirs(d, exist_ok=True)

        # --- A real 1x1 PNG for upload tests ---
        _write_test_png(os.path.join(images_dir, "test_photo.png"))

        # --- main.md ---
        main_md = os.path.join(tmp, "main.md")
        with open(main_md, "w") as f:
            f.write("# Engineering Notebook\n\n")
            f.write("- [My First Build](2026_01_01_my_first_build.md)\n")
            f.write("- [Reading the docs](2026_01_02_reading_the_docs.md)\n")

        # --- A linked page with mixed media content ---
        page_path = os.path.join(tmp, "2026_01_01_my_first_build.md")
        with open(page_path, "w") as f:
            f.write("# My First Build\n\n")
            f.write("Some intro text:\n\n")
            f.write("- relative image: ![photo](images/test_photo.png)\n")
            f.write("- root-relative image: ![photo](/images/test_photo.png)\n")
            f.write("- legacy /media/ image: ![photo](/media/images/test_photo.png)\n")
            f.write("- video: <video width=\"640\" loop autoplay controls>"
                    "<source src=\"videos/test.webm\" type=\"video/webm\"></video>\n")
            f.write("- root-relative video: <video width=\"640\" loop autoplay controls>"
                    "<source src=\"/videos/test.webm\" type=\"video/webm\"></video>\n")
            f.write("- legacy /media/ video: <video width=\"640\" loop autoplay controls>"
                    "<source src=\"/media/videos/test.webm\" type=\"video/webm\"></video>\n")
            f.write("- figure: ![diagram](figures/test.drawio.svg)\n")
            f.write("- root-relative figure: ![diagram](/figures/test.drawio.svg)\n")
            f.write("- external image: ![ext](https://example.com/img.png)\n\n")
            f.write("[Another page](2026_01_02_reading_the_docs.md)\n")

        # --- A second page for link tests ---
        page2_path = os.path.join(tmp, "2026_01_02_reading_the_docs.md")
        with open(page2_path, "w") as f:
            f.write("# Reading the Docs\n\nHello world.\n")

        # --- .qmd_conf ---
        config = {
            "notebook_title": "Test Notebook",
            "default_image_width": 600,
            "local": {
                "md_path": ".",
                "images_path": "images",
                "videos_path": "videos",
                "figures_path": "figures",
                "files_path": "files",
                "main_md": "main.md",
            },
            "global": {
                "images_dir": "~/Pictures/Screenshots/",
                "videos_dir": "~/Videos",
            },
            "theme": {
                "base": "#f4f5f7",
                "surface": "#ffffff",
                "accent": "#3498db",
            },
            "Images": ["images/test_photo.png"],
            "Videos": [],
            "Drawio": [],
            "Markdown": [
                {"filename": "2026_01_01_my_first_build.md", "title": "My First Build"},
                {"filename": "2026_01_02_reading_the_docs.md", "title": "Reading the Docs"},
            ],
        }
        config_path = os.path.join(tmp, ".qmd_conf")
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)

        # --- Boot the Flask test client ---
        from utils.configurations_manager import ConfigurationManager
        cm = ConfigurationManager()
        # Override paths to our temp dir
        cm.config_path = config_path
        cm.config_raw = config.copy()
        cm.sub_config_paths()

        from web_server import WebServer
        server = WebServer(cm, host="127.0.0.1", port=9999, password=None)

        client = server.app.test_client()
        # Stash references the tests need
        client._tmp_dir = tmp
        client._config_path = config_path
        client._images_dir = images_dir
        client._videos_dir = videos_dir
        client._figures_dir = figures_dir
        yield client

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Minimal 1x1 transparent PNG (67 bytes)
_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _write_test_png(path):
    with open(path, "wb") as f:
        f.write(_PNG_BYTES)


# ===================================================================
# Tests
# ===================================================================

class TestPageViewing:
    """Page rendering: view page, markdown-to-HTML, media path fixes."""

    def test_home_redirects_to_main(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 302
        assert "/page/main.md" in resp.headers["Location"]

    def test_view_main_page(self, app_client):
        resp = app_client.get("/page/main.md")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Engineering Notebook" in html

    def test_view_subpage(self, app_client):
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "My First Build" in html

    def test_404_for_missing_page(self, app_client):
        resp = app_client.get("/page/nonexistent.md")
        assert resp.status_code == 404

    # -- Media path normalization in rendered HTML --

    def test_relative_image_path_gets_leading_slash(self, app_client):
        """Markdown '![alt](images/photo.png)' -> HTML src="/images/photo.png"."""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        assert 'src="/images/test_photo.png"' in html

    def test_root_relative_image_path_preserved(self, app_client):
        """Markdown '![alt](/images/photo.png)' -> HTML src="/images/photo.png"."""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        # Already root-relative, should stay root-relative
        assert 'src="/images/test_photo.png"' in html

    def test_legacy_media_prefix_stripped(self, app_client):
        """Markdown '![alt](/media/images/photo.png)' -> HTML src="/images/photo.png"."""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        # Should NOT contain /media/ anywhere in src attributes
        assert 'src="/media/' not in html

    def test_relative_video_path_gets_leading_slash(self, app_client):
        """<source src="videos/..."> -> <source src="/videos/...">"""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        assert 'src="/videos/test.webm"' in html

    def test_root_relative_video_path_preserved(self, app_client):
        """<source src="/videos/..."> stays as /videos/..."""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        assert 'src="/videos/test.webm"' in html

    def test_legacy_media_video_stripped(self, app_client):
        """<source src="/media/videos/..."> -> <source src="/videos/...">"""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        assert 'src="/media/' not in html

    def test_figure_path_gets_leading_slash(self, app_client):
        """![alt](figures/diagram.svg) -> src="/figures/diagram.svg"."""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        assert 'src="/figures/test.drawio.svg"' in html

    def test_external_url_untouched(self, app_client):
        """External URLs (https://...) must never be rewritten."""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        assert 'src="https://example.com/img.png"' in html

    def test_page_links_are_not_broken(self, app_client):
        """Relative page links like [page](other.md) must not be mangled."""
        resp = app_client.get("/page/2026_01_01_my_first_build.md")
        html = resp.data.decode()
        # The markdown link should still point to the .md file
        assert "2026_01_02_reading_the_docs.md" in html


class TestMediaServing:
    """Static media files are served from the correct URL paths."""

    def test_image_served_via_direct_route(self, app_client):
        """GET /images/test_photo.png returns the image."""
        resp = app_client.get("/images/test_photo.png")
        assert resp.status_code == 200
        assert resp.content_type.startswith("image/")

    def test_image_served_via_media_prefix(self, app_client):
        """GET /media/images/test_photo.png (legacy) also works."""
        resp = app_client.get("/media/images/test_photo.png")
        assert resp.status_code == 200

    def test_image_404_for_missing(self, app_client):
        resp = app_client.get("/images/no_such_file.png")
        assert resp.status_code == 404

    def test_video_dir_served(self, app_client):
        """The /videos/ route exists (empty dir, but route is registered)."""
        # No video files in our test fixture, so we just test a 404
        resp = app_client.get("/videos/no_such.webm")
        assert resp.status_code == 404

    def test_figures_dir_served(self, app_client):
        resp = app_client.get("/figures/no_such.svg")
        assert resp.status_code == 404


class TestPageEditing:
    """Create, edit, and save pages."""

    def test_edit_page_loads(self, app_client):
        resp = app_client.get("/edit/2026_01_01_my_first_build.md")
        assert resp.status_code == 200
        assert "My First Build" in resp.data.decode()

    def test_save_page(self, app_client, tmp_path):
        """POST /save/<filename> updates the file on disk."""
        new_content = "# Updated Title\n\nNew body text."
        resp = app_client.post(
            "/save/2026_01_01_my_first_build.md",
            data={"content": new_content},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        # Verify the file was actually written
        fpath = os.path.join(app_client._tmp_dir, "2026_01_01_my_first_build.md")
        with open(fpath) as f:
            assert f.read() == new_content

    def test_new_page_creates_file(self, app_client):
        resp = app_client.post("/new_page", data={"title": "Brand New Page"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        # File should exist on disk
        fname = data["filename"]
        assert os.path.exists(os.path.join(app_client._tmp_dir, fname))

    def test_new_page_rejects_empty_title(self, app_client):
        resp = app_client.post("/new_page", data={"title": "  "})
        data = resp.get_json()
        assert data["success"] is False

    def test_new_page_rejects_duplicate(self, app_client):
        # Create once
        app_client.post("/new_page", data={"title": "Duplicate Test"})
        # Create again — should fail
        resp = app_client.post("/new_page", data={"title": "Duplicate Test"})
        data = resp.get_json()
        assert data["success"] is False


class TestEditorInsertionHelpers:
    """Client-side insert helpers rendered on /edit/<page>.

    The media sidebar's Insert buttons paste markdown via these helpers, so
    the behaviour of the vendored JavaScript is pinned here:

      - page links are inserted with RELATIVE paths (no leading slash) so
        they work in offline markdown viewers;
      - inserted <video> tags are centered via an inline style;
      - the Vim extension is registered before basicSetup so its Ctrl+d /
        Ctrl+u half-page scroll motions are not shadowed by basicSetup's
        Mod-d (selectNextOccurrence) / Mod-u (undoSelection) bindings.
    """

    def _edit_page(self, app_client):
        resp = app_client.get("/edit/2026_01_01_my_first_build.md")
        assert resp.status_code == 200
        return resp.data.decode()

    @staticmethod
    def _function_body(page, name):
        """Return one top-level function's source (definition .. next def)."""
        marker = f"function {name}"
        start = page.index(marker)
        try:
            end = page.index("function ", start + len(marker))
        except ValueError:
            # Last function on the page: run through the closing script tag.
            end = page.index("</script>", start)
        body = page[start:end]
        # Drop line comments so tests assert on code, not prose.
        return re.sub(r"^\s*//.*$", "", body, flags=re.MULTILINE)

    def test_page_links_are_relative(self, app_client):
        """insertPageLink strips the leading slash before building the link."""
        body = self._function_body(self._edit_page(app_client), "insertPageLink")
        assert "replace(/^\\/+/," in body
        # The link template must use the stripped path, not the raw one.
        assert "[${title}](${rel})" in body
        assert "[${title}](${path})" not in body

    def test_video_tags_are_centered(self, app_client):
        """The video literal carries the same centering style as <img>."""
        body = self._function_body(self._edit_page(app_client), "insertMedia")
        # Every media tag generated by insertMedia exposes the style on its
        # opening tag.
        for tag in re.findall(r"<(?:video|img)\b[^>]*>", body):
            assert 'style="display:block; margin:0 auto;"' in tag, tag

    def test_vim_registered_before_basic_setup(self, app_client):
        """The vim compartment must precede basicSetup or Ctrl+d/Ctrl+u are
        swallowed by basicSetup's Mod-d/Mod-u keymap bindings."""
        body = self._function_body(self._edit_page(app_client), "buildExtensions")
        assert "vimCompartment.of" in body and "basicSetup" in body
        assert body.index("vimCompartment.of") < body.index("basicSetup")


class TestImageUpload:
    """Image upload endpoint and markdown link generation."""

    def test_upload_image_success(self, app_client):
        png_data = _PNG_BYTES
        resp = app_client.post(
            "/upload_image",
            data={
                "title": "Test Upload",
                "file": (io.BytesIO(png_data), "upload.png"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        # The markdown link must use a relative path (no leading /)
        link = data["markdown_link"]
        assert link.startswith("![Test Upload](")
        # Must NOT start with /images/ — should be images/...
        path = link.split("(")[1].rstrip(")")
        assert not path.startswith("/"), f"Upload link must be relative, got: {link}"
        assert path.startswith("images/"), f"Upload link path unexpected: {link}"

    def test_upload_image_file_exists(self, app_client):
        """The uploaded file should actually land in the images directory."""
        resp = app_client.post(
            "/upload_image",
            data={
                "title": "File Check",
                "file": (io.BytesIO(_PNG_BYTES), "check.png"),
            },
            content_type="multipart/form-data",
        )
        data = resp.get_json()
        assert data["success"] is True
        rel_path = data["relative_path"]
        full_path = os.path.join(app_client._tmp_dir, rel_path)
        assert os.path.exists(full_path)

    def test_upload_image_no_file(self, app_client):
        resp = app_client.post("/upload_image", data={"title": "No File"})
        data = resp.get_json()
        assert data["success"] is False

    def test_upload_image_no_title(self, app_client):
        resp = app_client.post(
            "/upload_image",
            data={
                "file": (io.BytesIO(_PNG_BYTES), "notitle.png"),
            },
            content_type="multipart/form-data",
        )
        data = resp.get_json()
        assert data["success"] is False


class TestDrawioEndpoints:
    """Draw.io diagram creation, loading, and saving."""

    _SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100" fill="red"/>'
        "</svg>"
    )
    _SVG_WITH_CONTENT = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
        'content="&lt;mxGraphModel&gt;&lt;root/&gt;&lt;/mxGraphModel&gt;">'
        "<rect width=\"100\" height=\"100\" fill=\"red\"/>"
        "</svg>"
    )

    def test_new_drawio_page_loads(self, app_client):
        resp = app_client.get("/new_drawio")
        assert resp.status_code == 200

    def test_save_drawio_new(self, app_client):
        resp = app_client.post(
            "/save_drawio_new",
            json={
                "title": "Test Diagram",
                "svg": self._SVG,
                "xml": "<mxGraphModel><root/></mxGraphModel>",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        # Markdown link must be relative (no leading /)
        link = data["markdown_link"]
        path = link.split("](")[1].rstrip(")")
        assert not path.startswith("/"), f"Drawio link must be relative, got: {link}"

        # File should exist
        rel = data["relative_path"]
        assert os.path.exists(os.path.join(app_client._tmp_dir, rel))

    def test_save_drawio_new_no_svg(self, app_client):
        resp = app_client.post(
            "/save_drawio_new",
            json={"title": "No SVG", "svg": "", "xml": ""},
        )
        data = resp.get_json()
        assert data["success"] is False

    def test_save_drawio_new_duplicate(self, app_client):
        app_client.post(
            "/save_drawio_new",
            json={"title": "Dup Diagram", "svg": self._SVG, "xml": "x"},
        )
        resp = app_client.post(
            "/save_drawio_new",
            json={"title": "Dup Diagram", "svg": self._SVG, "xml": "x"},
        )
        data = resp.get_json()
        assert data["success"] is False
        assert "already exists" in data["message"]

    def test_edit_drawio_page_loads(self, app_client):
        # Create a diagram first
        save_resp = app_client.post(
            "/save_drawio_new",
            json={"title": "Edit Test", "svg": self._SVG, "xml": "x"},
        )
        rel_path = save_resp.get_json()["relative_path"]

        resp = app_client.get(f"/edit_drawio/{rel_path}")
        assert resp.status_code == 200

    def test_edit_drawio_404(self, app_client):
        resp = app_client.get("/edit_drawio/no_such_file.drawio.svg")
        assert resp.status_code == 404

    def test_save_drawio_existing(self, app_client):
        # Create
        save_resp = app_client.post(
            "/save_drawio_new",
            json={"title": "Update Me", "svg": self._SVG, "xml": "x"},
        )
        rel_path = save_resp.get_json()["relative_path"]

        # Update
        resp = app_client.post(
            f"/save_drawio/{rel_path}",
            json={"svg": self._SVG_WITH_CONTENT, "xml": "updated"},
        )
        data = resp.get_json()
        assert data["success"] is True


class TestSearch:
    """Full-text search endpoint."""

    def test_search_finds_matching_page(self, app_client):
        resp = app_client.get("/search?q=Build")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "My First Build" in html

    def test_search_no_results(self, app_client):
        resp = app_client.get("/search?q=zzzzzznonexistent")
        html = resp.data.decode()
        # Should still render, just with no results
        assert resp.status_code == 200


class TestMarkdownPreview:
    """API endpoint for live preview rendering."""

    def test_preview_renders_markdown(self, app_client):
        resp = app_client.post(
            "/api/markdown_preview",
            json={"content": "Hello **world**"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "<strong>world</strong>" in data["html"]

    def test_preview_renders_tables_as_thead_tbody(self, app_client):
        """Markdown tables become real <table> elements with <thead>/<th> and
        <tbody>/<td> — the structure the CSS targets for its header rule,
        bold header text, and column dividers. Markdown column alignment
        (|:---:|) is preserved as inline styles so it outranks the base
        left alignment from the stylesheet."""
        content = (
            "| Left | Center | Right |\n"
            "|------|:------:|------:|\n"
            "| a    | b      | c     |\n"
        )
        resp = app_client.post("/api/markdown_preview", json={"content": content})
        assert resp.status_code == 200
        html = resp.get_json()["html"]
        assert "<table>" in html
        assert "<thead>" in html
        assert "<th>Left</th>" in html
        assert "<tbody>" in html
        assert "<td>a</td>" in html
        assert '<th style="text-align: center;">Center</th>' in html

    def test_preview_normalizes_media_paths(self, app_client):
        """The preview API must also convert relative paths to root-relative."""
        resp = app_client.post(
            "/api/markdown_preview",
            json={"content": "![alt](images/photo.png)"},
        )
        data = resp.get_json()
        assert 'src="/images/photo.png"' in data["html"]

    def test_preview_strips_legacy_media_prefix(self, app_client):
        resp = app_client.post(
            "/api/markdown_preview",
            json={"content": '![alt](/media/images/photo.png)'},
        )
        data = resp.get_json()
        assert 'src="/images/photo.png"' in data["html"]
        assert "/media/" not in data["html"]


class TestMediaListAPI:
    """The /api/media_list endpoint returns registered media metadata."""

    def test_media_list_includes_images(self, app_client):
        resp = app_client.get("/api/media_list?tab=images")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_media_list_search_filter(self, app_client):
        resp = app_client.get("/api/media_list?q=test_photo")
        data = resp.get_json()
        assert data["total"] >= 1

    def test_media_list_pages_tab(self, app_client):
        resp = app_client.get("/api/media_list?tab=pages")
        data = resp.get_json()
        assert data["total"] >= 2

    def test_media_list_paths_are_relative(self, app_client):
        """Sidebar items expose relative paths; the client inserts these into
        markdown, so a leading slash would break offline viewers and page
        links."""
        items = app_client.get("/api/media_list?tab=pages").get_json()["items"]
        assert items, "expected at least one page in the fixture"
        for item in items:
            assert not item["path"].startswith("/"), item["path"]
        imgs = app_client.get("/api/media_list?tab=images").get_json()["items"]
        for item in imgs:
            assert not item["path"].startswith("/"), item["path"]


class TestStyleEndpoint:
    """The /style.css endpoint serves custom or default CSS."""

    def test_style_css_returns_css(self, app_client):
        resp = app_client.get("/style.css")
        assert resp.status_code == 200
        assert "text/css" in resp.content_type

    def test_style_css_includes_table_styling(self, app_client):
        """The default stylesheet must style markdown tables: centered tables
        with roomy cells, bold centered headers, column dividers, and a
        single rule under the header row. With no .qmd.css present this
        endpoint serves the bundled default."""
        css = app_client.get("/style.css").data.decode()
        # Table block exists and centers the table in the page.
        table_block = re.search(
            r"\.markdown-content table\s*\{([^}]*)\}", css)
        assert table_block, "missing .markdown-content table rules"
        assert re.search(r"margin:\s*1rem\s+auto", table_block.group(1))
        # Cells get padding and vertical dividers.
        cell_block = re.search(
            r"\.markdown-content th,\s*\.markdown-content td\s*\{([^}]*)\}", css)
        assert cell_block, "missing th/td rules"
        assert re.search(r"padding:\s*0\.5rem\s+1rem", cell_block.group(1))
        assert re.search(r"border-left:\s*1px\s+solid\s+var\(--c-border\)",
                         cell_block.group(1))
        # Bold, centered headers, and one rule between header and body.
        th_block = re.search(r"\.markdown-content th\s*\{([^}]*)\}", css)
        assert th_block, "missing th rules"
        assert re.search(r"font-weight:\s*700", th_block.group(1))
        assert re.search(r"text-align:\s*center", th_block.group(1))
        assert re.search(
            r"\.markdown-content thead th\s*\{[^}]*border-bottom:\s*2px\s+solid\s+var\(--c-border\)",
            css, re.S)


class TestHandlerFunctions:
    """Direct tests on the utility functions that generate markdown/HTML links.

    These ensure that the source markdown uses relative paths (no leading /)
    for offline viewer compatibility, while the web renderer adds the / back.
    """

    def test_image_link_is_relative(self):
        from utils.image_handler import create_markdown_image_link
        link = create_markdown_image_link("Photo", "images/photo.png")
        assert link == "![Photo](images/photo.png)"

    def test_image_link_strips_leading_slash(self):
        from utils.image_handler import create_markdown_image_link
        link = create_markdown_image_link("Photo", "/images/photo.png")
        assert link == "![Photo](images/photo.png)"

    def test_video_tag_is_relative(self):
        from utils.video_handler import create_video_html_tag
        tag = create_video_html_tag("videos/clip.webm")
        assert 'src="videos/clip.webm"' in tag

    def test_video_tag_strips_leading_slash(self):
        from utils.video_handler import create_video_html_tag
        tag = create_video_html_tag("/videos/clip.webm")
        assert 'src="videos/clip.webm"' in tag

    def test_drawio_link_is_relative(self):
        from utils.drawio_handler import create_markdown_link
        link = create_markdown_link("Diagram", "figures/test.drawio.svg")
        assert link == "![Diagram](figures/test.drawio.svg)"

    def test_drawio_link_strips_leading_slash(self):
        from utils.drawio_handler import create_markdown_link
        link = create_markdown_link("Diagram", "/figures/test.drawio.svg")
        assert link == "![Diagram](figures/test.drawio.svg)"


class TestDrawioHandler:
    """Draw.io SVG round-trip: extract, ensure, write."""

    def test_extract_embedded_xml_from_svg_with_content(self):
        from utils.drawio_handler import extract_embedded_xml
        svg = '<svg content="&lt;mxGraphModel/&gt;"><rect/></svg>'
        assert extract_embedded_xml(svg) == "<mxGraphModel/>"

    def test_extract_embedded_xml_returns_none_for_plain_svg(self):
        from utils.drawio_handler import extract_embedded_xml
        assert extract_embedded_xml("<svg><rect/></svg>") is None

    def test_write_embedded_svg_creates_file(self):
        from utils.drawio_handler import write_embedded_svg
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "test.drawio.svg")
            write_embedded_svg("<svg><rect/></svg>", path, fallback_xml="<mxGraphModel/>")
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "content=" in content  # fallback was injected
        finally:
            shutil.rmtree(tmp)

    def test_write_embedded_svg_rejects_non_svg(self):
        from utils.drawio_handler import write_embedded_svg
        with pytest.raises(ValueError, match="not a valid SVG"):
            write_embedded_svg("hello world", "/dev/null")


class TestDrawioEditorAutosave:
    """The draw.io editor autosaves and never exits without saving.

    Diagram edits live inside the cross-origin draw.io iframe, reachable only
    via the export roundtrip, so the behaviour is pinned by rendering
    /edit_drawio/<file> and inspecting the page's JavaScript:

      - a 60s autosave tick exports and saves only existing diagrams, and
        skips the request when the XML is unchanged;
      - the draw.io 'exit' event routes through saveDiagram() so the diagram
        is saved before the redirect (plain redirect only when nothing can
        be saved — editor still loading or untitled new diagram);
      - Cancel and beforeunload guard against losing unsaved edits.
    """

    _SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100" fill="red"/>'
        "</svg>"
    )

    def _editor_page(self, app_client):
        resp = app_client.post(
            "/save_drawio_new",
            json={
                "title": "Autosave Diagram",
                "svg": self._SVG,
                "xml": "<mxGraphModel><root/></mxGraphModel>",
            },
        )
        assert resp.status_code == 200
        rel = resp.get_json()["relative_path"]
        page = app_client.get("/edit_drawio/" + rel)
        assert page.status_code == 200
        return page.data.decode()

    def test_autosave_ticks_every_minute(self, app_client):
        page = self._editor_page(app_client)
        assert "setInterval(autosaveTick, 60000)" in page
        tick = TestEditorInsertionHelpers._function_body(page, "autosaveTick")
        # New diagrams (no filename yet) never autosave into existence.
        assert "IS_NEW" in tick
        assert "requestExport(" in tick

    def test_autosave_skips_unchanged_diagrams(self, app_client):
        """A tick whose export matches the last saved XML must not POST."""
        page = self._editor_page(app_client)
        handler = TestEditorInsertionHelpers._function_body(page, "handleExportedSvg")
        assert "autoSaveRunning && xml && xml === lastSavedXml" in handler
        # The unchanged path clears the in-flight flag and does not fetch.
        skip = handler[handler.index("xml === lastSavedXml"):handler.index("saveExisting")]
        assert "saveInFlight = false" in skip
        assert "fetch(" not in skip

    def test_exit_event_saves_before_leaving(self, app_client):
        page = self._editor_page(app_client)
        i = page.index("msg.event === 'exit'")
        branch = page[i:i + 800]
        assert "saveDiagram(true)" in branch
        # The save attempt happens before the (fallback) navigation.
        assert branch.index("saveDiagram(true)") < branch.index("window.location.href")

    def test_exit_save_redirects_to_diagram_list(self, app_client):
        """Save & Close (and exit-triggered saves) land on /drawio: the
        existing-file path after success, and the new-file path too (instead
        of redirecting into a fresh editor session)."""
        page = self._editor_page(app_client)
        existing = TestEditorInsertionHelpers._function_body(page, "saveExisting")
        assert existing.index("closeAfterSave") < existing.index("'/drawio'")
        new = TestEditorInsertionHelpers._function_body(page, "saveNew")
        compact = re.sub(r"\s+", " ", new)
        assert "closeAfterSave ? '/drawio' : '/edit_drawio/'" in compact

    def test_cancel_and_unload_guard_unsaved_changes(self, app_client):
        page = self._editor_page(app_client)
        cancel = TestEditorInsertionHelpers._function_body(page, "cancelEditing")
        assert "lastSeenXml !== lastSavedXml" in cancel
        assert "confirm(" in cancel
        assert 'onclick="return cancelEditing();"' in page
        unload = page[page.index("addEventListener('beforeunload'"):]
        unload = unload[:unload.index("\n}")]
        assert "lastSeenXml !== lastSavedXml" in unload
        assert "preventDefault()" in unload

    def test_autosave_status_indicator(self, app_client):
        """The nav shows a persistent autosave status like the page editor's.
        Existing diagrams start as 'Auto-save enabled'; success updates it to
        '✓ Auto-saved at HH:MM' / '✓ Saved at HH:MM' via updateAutosaveStatus
        (with a green .ok flash that reverts)."""
        page = self._editor_page(app_client)
        assert 'id="autosave-status"' in page
        assert "Auto-save enabled" in page
        # New diagrams: autosave only kicks in after the first save.
        new_page = app_client.get("/new_drawio").data.decode()
        assert "Auto-save starts after first save" in new_page
        fn = TestEditorInsertionHelpers._function_body(page, "updateAutosaveStatus")
        assert "classList.toggle('ok'" in fn or 'classList.toggle("ok"' in fn
        save_existing = TestEditorInsertionHelpers._function_body(page, "saveExisting")
        assert "updateAutosaveStatus('✓ Auto-saved at ' + t, true)" in save_existing
        assert "updateAutosaveStatus('✓ Saved at ' + t, true)" in save_existing


class TestPasswordProtection:
    """When a password is set, routes require auth."""

    @pytest.fixture()
    def password_client(self):
        tmp = tempfile.mkdtemp(prefix="qmd_pw_test_")
        try:
            config = {
                "notebook_title": "Locked",
                "default_image_width": 600,
                "local": {
                    "md_path": ".",
                    "images_path": "images",
                    "videos_path": "videos",
                    "figures_path": "figures",
                    "files_path": "files",
                    "main_md": "main.md",
                },
                "global": {"images_dir": "~/Pictures/", "videos_dir": "~/Videos"},
                "theme": {"base": "#f4f5f7", "surface": "#ffffff", "accent": "#3498db"},
                "Images": [],
                "Videos": [],
                "Drawio": [],
                "Markdown": [],
            }
            # Write main.md so the home redirect works
            with open(os.path.join(tmp, "main.md"), "w") as f:
                f.write("# Locked\n")
            for d in ("images", "videos", "figures"):
                os.makedirs(os.path.join(tmp, d), exist_ok=True)

            config_path = os.path.join(tmp, ".qmd_conf")
            with open(config_path, "w") as f:
                yaml.safe_dump(config, f)

            from utils.configurations_manager import ConfigurationManager
            from web_server import WebServer
            cm = ConfigurationManager()
            cm.config_path = config_path
            cm.config_raw = config.copy()
            cm.sub_config_paths()
            server = WebServer(cm, host="127.0.0.1", port=9998, password="s3cret")
            client = server.app.test_client()
            client._tmp_dir = tmp
            yield client
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_unauthenticated_redirects_to_login(self, password_client):
        resp = password_client.get("/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_login_with_wrong_password(self, password_client):
        resp = password_client.post("/login", data={"password": "wrong"})
        assert resp.status_code == 200  # re-renders login with error
        assert b"Invalid" in resp.data

    def test_login_with_correct_password(self, password_client):
        resp = password_client.post("/login", data={"password": "s3cret"})
        # Should redirect to home on success
        assert resp.status_code == 302
        assert "/" in resp.headers["Location"]

        # Subsequent requests should be authenticated
        home = password_client.get("/")
        assert home.status_code == 302
        assert "/page/main.md" in home.headers["Location"]

    def test_logout_clears_session(self, password_client):
        # Login first
        password_client.post("/login", data={"password": "s3cret"})
        # Logout
        password_client.get("/logout")
        # Now should redirect to login again
        resp = password_client.get("/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]