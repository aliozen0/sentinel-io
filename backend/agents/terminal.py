import paramiko
import asyncio
import logging
from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("TerminalManager")

class TerminalSession:
    def __init__(self, hostname, port, username, key_path=None, password=None, passphrase=None):
        self.hostname = hostname
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.channel = None
        
        try:
            # Setup Key
            pkey = None
            if key_path:
                pkey = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
            elif password is None and passphrase: # Direct key content handling setup later
                 pass

            self.client.connect(
                hostname=hostname,
                port=int(port),
                username=username,
                password=password,
                pkey=pkey,
                timeout=10
            )
            
            # Start Interactive Shell
            self.channel = self.client.invoke_shell()
            self.channel.setblocking(0) # Non-blocking
            logger.info(f"SSH Shell connected to {hostname}")
            
        except Exception as e:
            logger.error(f"SSH Connection Failed: {e}")
            raise e

    def send(self, command: str):
        if self.channel:
            self.channel.send(command + "\n")

    def recv(self, n=4096):
        if self.channel and self.channel.recv_ready():
            return self.channel.recv(n).decode('utf-8', errors='ignore')
        return None

    def close(self):
        if self.client:
            self.client.close()

class TerminalManager:
    """
    Manages active WebSocket -> SSH Terminal sessions.
    """
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}

    def create_session(self, session_id: str, config: dict):
        # In a real app, handle key content -> temp file or PKey obj
        # For Demo/Mock, we'll simulate if hostname is 'demo-server'
        if config.get("hostname") == "demo.io.net" or config.get("hostname") == "localhost":
             self.sessions[session_id] = MockTerminalSession()
             return

        # Real SSH
        # NOTE: Handling raw private key string requires io.StringIO
        import io
        pkey = None
        if config.get("privateKey"):
             try:
                # Strip potential whitespace
                pk_str = config["privateKey"].strip()
                pkey = paramiko.RSAKey.from_private_key(io.StringIO(pk_str), password=config.get("passphrase"))
             except Exception:
                # Fallback or other key types (Ed25519 etc not implemented here yet in TerminalManager)
                pass

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=config["hostname"],
                port=int(config.get("port", 22)),
                username=config["username"],
                password=config.get("password"),
                pkey=pkey,
                timeout=5,
                look_for_keys=False,
                allow_agent=False
            )
            channel = client.invoke_shell()
            channel.setblocking(0)
            
            self.sessions[session_id] = RealTerminalSession(client, channel)
            
        except Exception as e:
            logger.error(f"Failed to create terminal: {e}")
            raise e

    def get_session(self, session_id):
        return self.sessions.get(session_id)

    def close_session(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id].close()
            del self.sessions[session_id]

# --- Adapter Classes ---

class RealTerminalSession:
    def __init__(self, client, channel):
        self.client = client
        self.channel = channel
    
    def send(self, cmd):
        self.channel.send(cmd + "\n")
        
    def recv(self):
        if self.channel.recv_ready():
            return self.channel.recv(4096).decode('utf-8', errors='ignore')
        return None
        
    def close(self):
        self.client.close()

class MockTerminalSession:
    def __init__(self):
        self.history = []
        
    def send(self, cmd):
        self.last_cmd = cmd.strip()
        
    def recv(self):
        # Simple Mock Responses
        import time
        if hasattr(self, 'last_cmd'):
            cmd = self.last_cmd
            del self.last_cmd
            
            if cmd == "nvidia-smi":
                return """
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.154.05   Driver Version: 535.154.05   CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0  On |                  Off |
| 30%   45C    P8    28W / 450W |    450MiB / 24564MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+
user@io-guard:~$ """
            elif cmd == "ls":
                return "train.py  requirements.txt  logs/\nuser@io-guard:~$ "
            elif cmd == "whoami":
                return "root\nuser@io-guard:~$ "
            else:
                return f"{cmd}: command not found\nuser@io-guard:~$ "
        return None

    def close(self):
        pass

terminal_manager = TerminalManager()
