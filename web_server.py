import threading
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import markdown
import os
import re
from functools import wraps
from utils import image_handler, video_handler

class WebServer:
    def __init__(self, config_manager, host='0.0.0.0', port=5000, password=None):
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
        # Fix image tags: src="images/..." or src="videos/..." -> src="/media/images/..."
        html_content = re.sub(r'src="((?:images|videos)/[^"]+)"', r'src="/media/\1"', html_content)
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
    
    def _setup_routes(self):
        """Setup all Flask routes"""
        
        @self.app.context_processor
        def inject_password_protected():
            notebook_title = self.config_manager.config.get('notebook_title', 'Quick-md Notebook')
            return {
                'password_protected': self.password is not None,
                'notebook_title': notebook_title
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
            return render_template('images.html', images=images)
        
        @self.app.route('/videos')
        @self._check_password
        def list_videos():
            videos = self.config_manager.config.get('Videos', [])
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
                temp_filename = self.config_manager.sanitize_filename(title + "_temp", extension=original_ext)
                filename = self.config_manager.sanitize_filename(title, extension=".webm")
                
                dest_directory = self.config_manager.config['local']['videos_path']
                os.makedirs(dest_directory, exist_ok=True)
                
                temp_path = os.path.join(dest_directory, temp_filename)
                file.save(temp_path)
                
                dest_path = os.path.join(dest_directory, filename)
                
                success, process_msg = video_handler.process_video_with_ffmpeg(
                    temp_path, dest_path, resolution, compression, 
                    output_extension=".webm", async_process=False
                )
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                if not success:
                    return jsonify({'success': False, 'message': process_msg})
                
                # Auto-detect relative path
                md_path = self.config_manager.config['local']['md_path']
                relative_dir = os.path.relpath(dest_directory, md_path)
                relative_path = f"{relative_dir}/{filename}"
                self.config_manager.add_video_to_config(relative_path)
                
                video_tag = video_handler.create_video_html_tag(relative_path, width="640")
                
                return jsonify({
                    'success': True, 
                    'message': 'Video uploaded and processed successfully',
                    'video_tag': video_tag,
                    'relative_path': relative_path
                })
            
            return render_template('upload_video.html')
        
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
            return jsonify({'images': images, 'videos': videos})
    
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
