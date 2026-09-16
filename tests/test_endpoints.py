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


class TestStyleEndpoint:
    """The /style.css endpoint serves custom or default CSS."""

    def test_style_css_returns_css(self, app_client):
        resp = app_client.get("/style.css")
        assert resp.status_code == 200
        assert "text/css" in resp.content_type


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