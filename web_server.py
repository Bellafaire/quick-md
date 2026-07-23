import threading
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import markdown
import os
import re
import time
import glob
import json
from functools import wraps
from datetime import datetime
from utils import image_handler, video_handler, drawio_handler
from utils.theme import resolve_theme

# Absolute path to this application's own directory (the quick-md/ folder).
# Used to keep search / page listings from indexing the app's own docs.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

class WebServer:
    def __init__(self, config_manager, host='127.0.0.1', port=5000, password=None):
        self.config_manager = config_manager
        self.host = host
        self.port = port
        self.password = password
        self.app = Flask(__name__)
        self.app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
        self.app.secret_key = os.urandom(24)
        self.server_thread = None
        self.is_running = False
        self._setup_routes()
    
    def _check_password(self, f):
        """Decorator to check if user is authenticated"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if self.password and not session.get('authenticated'):
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def _fix_media_paths(self, html_content):
        """Convert relative media paths to absolute /media/ paths"""
        # Fix image/video tags: src="images/..." or src="videos/..." or src="figures/..." (draw.io diagrams) -> src="/media/..."
        html_content = re.sub(r'src="((?:images|videos|figures)/[^"]+)"', r'src="/media/\1"', html_content)
        # Fix markdown image syntax that got converted to HTML
        html_content = re.sub(r'<img alt="([^"]*)" src="([^"]+)"', lambda m: f'<img alt="{m.group(1)}" src="/media/{m.group(2)}"' if not m.group(2).startswith(('/media/', 'http')) else m.group(0), html_content)
        return html_content
    
    def _extract_title_from_markdown(self, content):
        """Extract the first H1 title from markdown content"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None

    def _snippets(self, content, qlower, max_snippets=3, radius=60):
        """Return up to `max_snippets` non-overlapping context snippets around matches of qlower."""
        snippets = []
        clower = content.lower()
        idx = 0
        while len(snippets) < max_snippets:
            pos = clower.find(qlower, idx)
            if pos == -1:
                break
            start = max(0, pos - radius)
            end = min(len(content), pos + len(qlower) + radius)
            snippet = content[start:end].replace('\n', ' ').strip()
            prefix = '…' if start > 0 else ''
            suffix = '…' if end < len(content) else ''
            snippets.append(prefix + snippet + suffix)
            # Skip past this snippet's window so the next snippet doesn't overlap it.
            idx = end
        return snippets

    def _search_markdown(self, query):
        """Full-text search across every .md file under md_path.

        Returns a list of dicts sorted by relevance (title hits weighted
        higher than body hits), each with filename, title, hit counts, and
        context snippets."""
        md_path = self.config_manager.config['local']['md_path']
        qlower = query.lower()
        results = []
        for root, dirs, files in os.walk(md_path):
            # Don't descend into the application's own directory.
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != APP_DIR]
            for name in files:
                if not name.endswith('.md'):
                    continue
                filepath = os.path.join(root, name)
                rel = os.path.relpath(filepath, md_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                except OSError:
                    continue
                title = self._extract_title_from_markdown(content) or name
                title_hits = title.lower().count(qlower)
                body_hits = content.lower().count(qlower)
                if title_hits == 0 and body_hits == 0:
                    continue
                results.append({
                    'filename': rel,
                    'title': title,
                    'title_hits': title_hits,
                    'body_hits': body_hits,
                    'score': title_hits * 10 + body_hits,
                    'snippets': self._snippets(content, qlower),
                })
        results.sort(key=lambda r: (-r['score'], r['title'].lower()))
        return results

    def _parse_progress(self, progress_file, meta_file):
        """Read ffmpeg -progress output + the duration sidecar and return
        (percent, speed) for a currently-encoding video."""
        duration = None
        try:
            if os.path.exists(meta_file):
                with open(meta_file) as f:
                    for line in f:
                        if line.startswith('duration='):
                            try:
                                duration = float(line.split('=', 1)[1].strip())
                            except ValueError:
                                pass
                            break
        except OSError:
            pass

        out_time = None
        speed = None
        try:
            if os.path.exists(progress_file):
                with open(progress_file) as f:
                    lines = f.read().splitlines()
                # The file appends over time; take the latest of each key.
                for line in reversed(lines):
                    if out_time is None and line.startswith('out_time='):
                        out_time = self._parse_hms(line.split('=', 1)[1].strip())
                    elif speed is None and line.startswith('speed='):
                        speed = line.split('=', 1)[1].strip()
                    if out_time is not None and speed is not None:
                        break
        except OSError:
            pass

        percent = None
        if duration and out_time is not None and duration > 0:
            percent = min(99, max(0, int(round(out_time / duration * 100))))
        return percent, speed

    @staticmethod
    def _parse_hms(s):
        """Parse HH:MM:SS(.frac) into seconds (float), or None."""
        parts = s.split(':')
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            return float(parts[0])
        except ValueError:
            return None

    def _page_details(self):
        """Build a list of markdown pages (newest first by mtime) for the
        editor sidebar's Pages tab."""
        md_path = self.config_manager.config['local']['md_path']
        result = []
        for root, dirs, files in os.walk(md_path):
            # Don't descend into the application's own directory.
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != APP_DIR]
            for name in files:
                if not name.endswith('.md'):
                    continue
                filepath = os.path.join(root, name)
                rel = os.path.relpath(filepath, md_path)
                try:
                    mtime = os.path.getmtime(filepath)
                except OSError:
                    mtime = 0
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                except OSError:
                    content = ''
                title = self._extract_title_from_markdown(content) or name
                result.append({
                    'path': rel,
                    'filename': name,
                    'title': title,
                    'timestamp': mtime,
                    'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M') if mtime else 'unknown',
                    'is_page': True,
                })
        result.sort(key=lambda x: x['timestamp'], reverse=True)
        return result

    def _media_details(self, paths, is_video):
        """Build a list of media detail dicts sorted by upload date (newest first).

        Uses the file's modification time on disk as a proxy for the upload
        date (files are written once on upload and not normally touched
        afterwards)."""
        md_path = self.config_manager.config['local']['md_path']
        result = []
        for p in paths:
            full = os.path.join(md_path, p)
            basename = os.path.basename(p)
            directory = os.path.dirname(full)
            exists = os.path.exists(full)
            if exists:
                try:
                    mtime = os.path.getmtime(full)
                except OSError:
                    mtime = 0
                processing = False
                failed = False
            else:
                # File not on disk yet. Distinguish "actively encoding" from
                # "failed/stale" by looking for the background process's
                # working files: the raw upload (.<name>.upload_*) and the
                # partial output (<name>.part*).
                working = glob.glob(os.path.join(directory, '.' + basename + '.upload_*')) \
                          + glob.glob(os.path.join(directory, basename + '.part*'))
                if working:
                    # Encode in progress -> treat as freshly uploaded so it
                    # sorts to the top of the sidebar.
                    processing = True
                    failed = False
                    mtime = time.time()
                else:
                    # Registered but no file and no working files -> the encode
                    # failed or was interrupted. Sort to the bottom; flag it so
                    # the UI can show "Failed" instead of "Processing…".
                    processing = False
                    failed = True
                    mtime = 0
            # For videos actively being encoded, surface live ffmpeg progress.
            progress_percent = None
            progress_speed = None
            if processing and is_video:
                progress_percent, progress_speed = self._parse_progress(
                    video_handler.progress_file_for(full),
                    video_handler.meta_file_for(full),
                )
            result.append({
                'path': p,
                'filename': basename,
                'timestamp': mtime,
                'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M') if (exists and mtime) else 'unknown',
                'is_video': is_video,
                'processing': processing,
                'failed': failed,
                'progress_percent': progress_percent,
                'progress_speed': progress_speed,
            })
        result.sort(key=lambda x: x['timestamp'], reverse=True)
        return result
    
    def _setup_routes(self):
        """Setup all Flask routes"""
        
        @self.app.context_processor
        def inject_password_protected():
            notebook_title = self.config_manager.config.get('notebook_title', 'Quick-md Notebook')
            theme = resolve_theme(self.config_manager.config.get('theme'))
            default_image_width = self.config_manager.config.get('default_image_width', 600)
            return {
                'password_protected': self.password is not None,
                'notebook_title': notebook_title,
                'theme': theme,
                'theme_json': json.dumps(theme),
                'default_image_width': default_image_width,
            }
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if not self.password:
                return redirect(url_for('index'))
            
            notebook_title = self.config_manager.config.get('notebook_title', 'Quick-md Notebook')
            
            if request.method == 'POST':
                password = request.form.get('password', '')
                if password == self.password:
                    session['authenticated'] = True
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error='Invalid password', notebook_title=notebook_title)
            
            return render_template('login.html', notebook_title=notebook_title)
        
        @self.app.route('/logout')
        def logout():
            session.pop('authenticated', None)
            return redirect(url_for('login'))
        
        @self.app.route('/')
        @self._check_password
        def index():
            from flask import redirect, url_for
            return redirect(url_for('view_page', filename='main.md'))
        
        @self.app.route('/page/<path:filename>')
        @self._check_password
        def view_page(filename):
            md_path = self.config_manager.config['local']['md_path']
            filepath = os.path.join(md_path, filename)
            
            if not os.path.exists(filepath):
                return "Page not found", 404
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            html_content = markdown.markdown(content, extensions=['extra'])
            html_content = self._fix_media_paths(html_content)
            
            # Extract page title
            page_title = self._extract_title_from_markdown(content) or filename
            
            return render_template('view_page.html', 
                                   filename=filename, 
                                   content=content, 
                                   html_content=html_content,
                                   page_title=page_title)
        
        @self.app.route('/edit/<path:filename>')
        @self._check_password
        def edit_page(filename):
            md_path = self.config_manager.config['local']['md_path']
            filepath = os.path.join(md_path, filename)
            
            if not os.path.exists(filepath):
                return "Page not found", 404
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Extract page title
            page_title = self._extract_title_from_markdown(content) or filename
            
            return render_template('edit_page.html', filename=filename, content=content, page_title=page_title)
        
        @self.app.route('/save/<path:filename>', methods=['POST'])
        @self._check_password
        def save_page(filename):
            md_path = self.config_manager.config['local']['md_path']
            filepath = os.path.join(md_path, filename)
            
            content = request.form.get('content', '')
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            return jsonify({'success': True, 'message': 'Page saved successfully'})
        
        @self.app.route('/new_page', methods=['GET', 'POST'])
        @self._check_password
        def new_page():
            if request.method == 'POST':
                title = request.form.get('title', '').strip()
                if not title:
                    return jsonify({'success': False, 'message': 'Title is required'})
                
                filename = self.config_manager.sanitize_filename(title, extension=".md")
                filepath = os.path.join(self.config_manager.config['local']['md_path'], filename)
                
                if os.path.exists(filepath):
                    return jsonify({'success': False, 'message': 'A page with this name already exists'})
                
                title_string = f"{self.config_manager.get_date_string()} {title}"
                
                with open(filepath, 'w') as file:
                    file.write(f"# {title_string}\n\n")
                
                with open(self.config_manager.config['local']['main_md'], 'a') as main_file:
                    main_file.write(f"- [{title_string}]({filename})\n")
                
                self.config_manager.add_markdown_to_config(filename, original_title=title)
                
                return jsonify({'success': True, 'filename': filename})
            
            return render_template('new_page.html')
        
        @self.app.route('/images')
        @self._check_password
        def list_images():
            images = self.config_manager.config.get('Images', [])
            # Sort newest first by file mtime
            md_path = self.config_manager.config['local']['md_path']
            images = sorted(images, key=lambda p: os.path.getmtime(os.path.join(md_path, p)) if os.path.exists(os.path.join(md_path, p)) else 0, reverse=True)
            return render_template('images.html', images=images)
        
        @self.app.route('/videos')
        @self._check_password
        def list_videos():
            videos = self.config_manager.config.get('Videos', [])
            # Sort newest first by file mtime
            md_path = self.config_manager.config['local']['md_path']
            videos = sorted(videos, key=lambda p: os.path.getmtime(os.path.join(md_path, p)) if os.path.exists(os.path.join(md_path, p)) else 0, reverse=True)
            return render_template('videos.html', videos=videos)
        
        @self.app.route('/upload_image', methods=['GET', 'POST'])
        @self._check_password
        def upload_image():
            if request.method == 'POST':
                if 'file' not in request.files:
                    return jsonify({'success': False, 'message': 'No file provided'})
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'message': 'No file selected'})
                
                title = request.form.get('title', '').strip()
                if not title:
                    return jsonify({'success': False, 'message': 'Title is required'})
                
                original_ext = '.' + file.filename.rsplit('.', 1)[1].lower()
                filename = self.config_manager.sanitize_filename(title, extension=original_ext)
                
                dest_directory = self.config_manager.config['local']['images_path']
                os.makedirs(dest_directory, exist_ok=True)
                
                dest_path = os.path.join(dest_directory, filename)
                file.save(dest_path)
                
                # Auto-detect relative path
                md_path = self.config_manager.config['local']['md_path']
                relative_dir = os.path.relpath(dest_directory, md_path)
                relative_path = f"{relative_dir}/{filename}"
                self.config_manager.add_image_to_config(relative_path)
                
                markdown_link = image_handler.create_markdown_image_link(title, relative_path)
                
                return jsonify({
                    'success': True, 
                    'message': 'Image uploaded successfully',
                    'markdown_link': markdown_link,
                    'relative_path': relative_path
                })
            
            return render_template('upload_image.html')
        
        @self.app.route('/upload_video', methods=['GET', 'POST'])
        @self._check_password
        def upload_video():
            if request.method == 'POST':
                if 'file' not in request.files:
                    return jsonify({'success': False, 'message': 'No file provided'})
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'message': 'No file selected'})
                
                title = request.form.get('title', '').strip()
                if not title:
                    return jsonify({'success': False, 'message': 'Title is required'})
                
                resolution = request.form.get('resolution', '720p')
                compression = request.form.get('compression', 'medium')
                
                original_ext = '.' + file.filename.rsplit('.', 1)[1].lower()
                filename = self.config_manager.sanitize_filename(title, extension=".webm")
                
                dest_directory = self.config_manager.config['local']['videos_path']
                os.makedirs(dest_directory, exist_ok=True)
                
                dest_path = os.path.join(dest_directory, filename)
                
                # Save the raw upload to a unique working file (hidden, random
                # suffix) so multiple uploads can be processed concurrently
                # without colliding. The background ffmpeg cleans this up.
                import string as _string, random as _random
                suffix = ''.join(_random.choices(_string.ascii_lowercase + _string.digits, k=8))
                work_name = f".{filename}.upload_{suffix}{original_ext}"
                work_path = os.path.join(dest_directory, work_name)
                file.save(work_path)
                
                # Probe the source duration up front so the sidebar can show a
                # live encode percentage (out_time / duration). Write it to a
                # per-job meta sidecar; the background ffmpeg cleans it up.
                duration = video_handler.get_video_duration(work_path)
                if duration:
                    try:
                        with open(video_handler.meta_file_for(dest_path), "w") as mf:
                            mf.write(f"duration={duration}\n")
                    except OSError:
                        pass
                
                # Register the final path in the config *now* so it shows up in
                # the media sidebar immediately and can be inserted at will.
                md_path = self.config_manager.config['local']['md_path']
                relative_dir = os.path.relpath(dest_directory, md_path)
                relative_path = f"{relative_dir}/{filename}"
                self.config_manager.add_video_to_config(relative_path)
                
                # Kick off ffmpeg in the background; return immediately so the
                # user can keep editing / start another upload. The video will
                # only be playable once the background encode finishes.
                success, process_msg = video_handler.process_video_with_ffmpeg(
                    work_path, dest_path, resolution, compression, 
                    output_extension=".webm", async_process=True,
                )
                
                if not success:
                    return jsonify({'success': False, 'message': process_msg})
                
                video_tag = video_handler.create_video_html_tag(relative_path, width="640")
                
                return jsonify({
                    'success': True, 
                    'message': 'Upload complete. Video is processing in the background; it will appear once ready.',
                    'video_tag': video_tag,
                    'relative_path': relative_path,
                    'processing': True,
                })
            
            return render_template('upload_video.html')
        
        @self.app.route('/search')
        @self._check_password
        def search():
            q = request.args.get('q', '').strip()
            results = self._search_markdown(q) if q else []
            return render_template('search.html', query=q, results=results)

        @self.app.route('/drawio')
        @self._check_password
        def list_drawio():
            diagrams = self.config_manager.config.get('Drawio', [])
            # Sort newest first by file mtime
            md_path = self.config_manager.config['local']['md_path']
            diagrams = sorted(diagrams, key=lambda p: os.path.getmtime(os.path.join(md_path, p)) if os.path.exists(os.path.join(md_path, p)) else 0, reverse=True)
            return render_template('drawio.html', diagrams=diagrams)

        @self.app.route('/new_drawio')
        @self._check_password
        def new_drawio():
            return render_template('drawio_editor.html', filename=None, page_title='New Diagram', initial_xml='')

        @self.app.route('/edit_drawio/<path:filename>')
        @self._check_password
        def edit_drawio(filename):
            md_path = self.config_manager.config['local']['md_path']
            filepath = os.path.join(md_path, filename)
            if not os.path.exists(filepath):
                return "Diagram not found", 404
            with open(filepath, 'r', encoding='utf-8') as f:
                svg = f.read()
            initial_xml = drawio_handler.extract_embedded_xml(svg) or ''
            title = os.path.basename(filename)
            return render_template('drawio_editor.html', filename=filename, page_title=title, initial_xml=initial_xml)

        @self.app.route('/save_drawio_new', methods=['POST'])
        @self._check_password
        def save_drawio_new():
            data = request.get_json(silent=True) or {}
            title = (data.get('title') or '').strip()
            svg = data.get('svg') or ''
            xml = data.get('xml') or ''
            if not title:
                return jsonify({'success': False, 'message': 'Title is required'})
            if not svg:
                return jsonify({'success': False, 'message': 'No diagram content provided'})

            filename = self.config_manager.sanitize_filename(title, extension='.drawio.svg')
            dest_directory = self.config_manager.config['local']['figures_path']
            os.makedirs(dest_directory, exist_ok=True)
            dest_path = os.path.join(dest_directory, filename)
            # Avoid clobbering an existing diagram silently.
            if os.path.exists(dest_path):
                return jsonify({'success': False, 'message': 'A diagram with this name already exists'})

            try:
                drawio_handler.write_embedded_svg(svg, dest_path, fallback_xml=xml)
            except ValueError as e:
                return jsonify({'success': False, 'message': str(e)})

            md_path = self.config_manager.config['local']['md_path']
            relative_dir = os.path.relpath(dest_directory, md_path)
            relative_path = f"{relative_dir}/{filename}"
            self.config_manager.add_drawio_to_config(relative_path)

            markdown_link = f"![{title}]({relative_path})"
            return jsonify({
                'success': True,
                'message': 'Diagram saved successfully',
                'markdown_link': markdown_link,
                'relative_path': relative_path,
                'filename': filename,
            })

        @self.app.route('/save_drawio/<path:filename>', methods=['POST'])
        @self._check_password
        def save_drawio(filename):
            md_path = self.config_manager.config['local']['md_path']
            filepath = os.path.join(md_path, filename)
            if not os.path.exists(filepath):
                return jsonify({'success': False, 'message': 'Diagram not found'}), 404
            data = request.get_json(silent=True) or {}
            svg = data.get('svg') or ''
            xml = data.get('xml') or ''
            if not svg:
                return jsonify({'success': False, 'message': 'No diagram content provided'})
            try:
                drawio_handler.write_embedded_svg(svg, dest_path=filepath, fallback_xml=xml)
            except ValueError as e:
                return jsonify({'success': False, 'message': str(e)})
            return jsonify({'success': True, 'message': 'Diagram saved successfully'})

        @self.app.route('/media/<path:filename>')
        @self._check_password
        def serve_media(filename):
            md_path = self.config_manager.config['local']['md_path']
            file_path = os.path.join(md_path, filename)
            
            if not os.path.exists(file_path):
                return "File not found", 404
            
            directory = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            return send_from_directory(directory, file_name)
        
        @self.app.route('/api/markdown_preview', methods=['POST'])
        @self._check_password
        def markdown_preview():
            content = request.json.get('content', '')
            html = markdown.markdown(content, extensions=['extra'])
            html = self._fix_media_paths(html)
            return jsonify({'html': html})
        
        @self.app.route('/api/media_list')
        @self._check_password
        def media_list():
            images = self.config_manager.config.get('Images', [])
            videos = self.config_manager.config.get('Videos', [])
            diagrams = self.config_manager.config.get('Drawio', [])
            image_details = self._media_details(images, is_video=False)
            video_details = self._media_details(videos, is_video=True)
            # Diagrams are static SVGs (no background processing), so reuse the
            # media-details helper with is_video=False to get timestamps/dates.
            diagram_details = self._media_details(diagrams, is_video=False)
            for d in diagram_details:
                d['is_drawio'] = True
            page_details = self._page_details()
            return jsonify({
                'images': image_details,
                'videos': video_details,
                'drawio': diagram_details,
                'pages': page_details,
            })
    
    def start(self):
        """Start the web server in a background thread"""
        if self.is_running:
            return
        
        def run_server():
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True
    
    def get_address(self):
        """Get the server address"""
        return f"http://{self.host}:{self.port}"
