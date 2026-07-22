FROM python:3.11-slim

# Install ffmpeg for video processing
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Accept build arguments for user/group IDs
ARG USER_ID=1000
ARG GROUP_ID=1000

# Create a non-root user with the same UID/GID as the host user
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash appuser

# Create and set permissions for notebook directory
RUN mkdir -p /notebook && \
    chown -R appuser:appuser /notebook

# Switch to non-root user
USER appuser

# Copy application code to /notebook/quick-md
WORKDIR /notebook/quick-md
COPY --chown=appuser:appuser . .

# Expose default port
EXPOSE 6580

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden in docker-compose or docker run).
# --network binds the Flask server to 0.0.0.0 *inside* the container, which
# is required for Docker port forwarding to reach it. Host-side exposure is
# controlled by the -p port mapping in run.sh / docker-compose.
CMD ["python3", "main.py", "--web-only", "--network"]
