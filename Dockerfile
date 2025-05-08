FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/razvanmacovei/k8s-multicluster-mcp"
LABEL org.opencontainers.image.description="Kubernetes Multi-Cluster MCP Server"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies directly with pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a directory for kubeconfig files
RUN mkdir -p /kubeconfigs

# Set default environment variables
ENV KUBECONFIG_DIR=/kubeconfigs

# Run the application
CMD ["python", "app.py"] 