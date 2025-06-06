# Multi-stage build for smaller final image
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy source code with proper ownership
COPY --chown=mcpuser:mcpuser . .

# Create kubeconfig directory
RUN mkdir -p /app/kubeconfigs && chown mcpuser:mcpuser /app/kubeconfigs

# Switch to non-root user
USER mcpuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV KUBECONFIG_DIR=/app/kubeconfigs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose port (though MCP typically uses stdio)
EXPOSE 8080

# Use python entrypoint
ENTRYPOINT ["python3", "app.py"]
