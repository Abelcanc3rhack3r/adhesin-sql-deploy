FROM python:3.11-slim

# Prevent python from buffering stdout/stderr (keeps your SQL prints real-time)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (caches this layer to speed up future builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your scripts, databases, and the structures folder
COPY . .

# Make the startup script executable
RUN chmod +x start.sh

# Expose the ports for backend and frontend
EXPOSE 8000 8501

# Launch the dual-server script
CMD ["./start.sh"]
