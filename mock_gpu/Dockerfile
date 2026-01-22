FROM python:3.9-slim-bookworm

# Install SSH Server, Wget, Curl, Ping
RUN apt-get update && apt-get install -y openssh-server wget curl iputils-ping nano && mkdir -p /var/run/sshd

# Configure SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Setup Root User .ssh
WORKDIR /root
RUN mkdir -p .ssh && chmod 700 .ssh

# Create startup script that generates keys dynamically
RUN echo '#!/bin/bash\n\
    \n\
    KEYS_DIR="/keys"\n\
    PRIVATE_KEY="$KEYS_DIR/demo_id_rsa"\n\
    PUBLIC_KEY="$KEYS_DIR/demo_id_rsa.pub"\n\
    \n\
    # Create keys directory if not exists\n\
    mkdir -p $KEYS_DIR\n\
    \n\
    # Generate key only if not exists (persistent across restarts)\n\
    if [ ! -f "$PRIVATE_KEY" ]; then\n\
    echo "Generating new SSH key pair..."\n\
    ssh-keygen -t rsa -b 2048 -f $PRIVATE_KEY -N "" -q\n\
    chmod 600 $PRIVATE_KEY\n\
    chmod 644 $PUBLIC_KEY\n\
    echo "SSH keys generated successfully!"\n\
    else\n\
    echo "Using existing SSH keys"\n\
    fi\n\
    \n\
    # Copy public key to authorized_keys\n\
    cp $PUBLIC_KEY /root/.ssh/authorized_keys\n\
    chmod 600 /root/.ssh/authorized_keys\n\
    \n\
    echo "Mock GPU Node ready. SSH enabled on port 22."\n\
    \n\
    # Start SSH daemon\n\
    exec /usr/sbin/sshd -D\n\
    ' > /entrypoint.sh && chmod +x /entrypoint.sh

# Expose SSH Port
EXPOSE 22

# Start with entrypoint
CMD ["/entrypoint.sh"]
