FROM python:3.9-slim

# Install SSH Server
RUN apt-get update && apt-get install -y openssh-server && \
    mkdir -p /run/sshd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy and setup entrypoint script
# Copy and setup entrypoint script
COPY start.sh /start.sh
RUN apt-get install -y dos2unix && dos2unix /start.sh && chmod +x /start.sh

# Use the startup script
ENTRYPOINT ["/start.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
