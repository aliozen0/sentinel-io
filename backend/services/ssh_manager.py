import paramiko
import io
import logging
import asyncio
from typing import Tuple, Optional, AsyncGenerator
from db.client import get_db

logger = logging.getLogger(__name__)


class SSHManager:
    """
    Handles secure connections to remote GPU nodes via Paramiko.
    Includes: Connection testing, File upload (SFTP), Command execution.
    """

    @staticmethod
    def _create_client_and_key(private_key_str: str) -> Tuple[paramiko.SSHClient, paramiko.PKey]:
        """
        Creates SSH client and parses private key.
        Returns (client, pkey) tuple.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        pkey = None
        # Try RSA first
        try:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str))
        except Exception:
            pass
        
        # Try Ed25519
        if not pkey:
            try:
                pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(private_key_str))
            except Exception:
                pass
        
        # Try ECDSA
        if not pkey:
            try:
                pkey = paramiko.ECDSAKey.from_private_key(io.StringIO(private_key_str))
            except Exception:
                pass
                
        if not pkey:
            raise ValueError("Invalid Private Key format. Supported: RSA, Ed25519, ECDSA (PEM format)")
        
        return client, pkey

    @staticmethod
    async def test_connection(
        hostname: str, 
        username: str, 
        private_key_str: str, 
        port: int = 22
    ) -> Tuple[bool, str]:
        """
        Attempts to establish an SSH connection and run 'uptime'.
        Returns (Success, Message).
        """
        try:
            client, pkey = SSHManager._create_client_and_key(private_key_str)
            
            logger.info(f"Connecting to {username}@{hostname}:{port}...")
            
            client.connect(
                hostname=hostname,
                port=port,
                username=username,
                pkey=pkey,
                timeout=10,
                banner_timeout=10
            )
            
            # Run simple command to verify shell access
            stdin, stdout, stderr = client.exec_command("uptime")
            output = stdout.read().decode().strip()
            
            client.close()
            return True, f"Connection Successful! Uptime: {output}"

        except paramiko.AuthenticationException:
            return False, "Authentication Failed (Wrong Key or User)"
        except paramiko.SSHException as e:
            return False, f"SSH Protocol Error: {str(e)}"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Connection Error: {str(e)}"

    @staticmethod
    async def upload_file(
        hostname: str,
        username: str,
        private_key_str: str,
        local_path: str,
        remote_path: str,
        port: int = 22
    ) -> Tuple[bool, str]:
        """
        Uploads a file to remote server via SFTP.
        Returns (Success, Message).
        """
        try:
            client, pkey = SSHManager._create_client_and_key(private_key_str)
            
            logger.info(f"SFTP: Connecting to {hostname}:{port}...")
            
            client.connect(
                hostname=hostname,
                port=port,
                username=username,
                pkey=pkey,
                timeout=15,
                banner_timeout=15
            )
            
            # Open SFTP session
            sftp = client.open_sftp()
            
            logger.info(f"SFTP: Uploading {local_path} -> {remote_path}")
            sftp.put(local_path, remote_path)
            
            # Verify file exists
            file_stat = sftp.stat(remote_path)
            file_size = file_stat.st_size
            
            sftp.close()
            client.close()
            
            return True, f"File uploaded successfully ({file_size} bytes)"
            
        except FileNotFoundError:
            return False, f"Local file not found: {local_path}"
        except paramiko.AuthenticationException:
            return False, "SFTP Authentication Failed"
        except paramiko.SSHException as e:
            return False, f"SFTP Error: {str(e)}"
        except Exception as e:
            return False, f"Upload Error: {str(e)}"

    @staticmethod
    async def execute_command(
        hostname: str,
        username: str,
        private_key_str: str,
        command: str,
        port: int = 22
    ) -> AsyncGenerator[str, None]:
        """
        Executes a command on remote server and yields output lines.
        Perfect for streaming to WebSocket.
        """
        client = None
        try:
            client, pkey = SSHManager._create_client_and_key(private_key_str)
            
            yield f"🔌 Connecting to {hostname}:{port}..."
            
            client.connect(
                hostname=hostname,
                port=port,
                username=username,
                pkey=pkey,
                timeout=15,
                banner_timeout=15
            )
            
            yield f"✅ Connected as {username}"
            yield f"🚀 Executing: {command}"
            yield "─" * 50
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            
            # Stream output line by line
            for line in iter(stdout.readline, ""):
                if line:
                    yield line.rstrip()
                await asyncio.sleep(0.01)  # Small delay to prevent blocking
            
            # Check for errors
            exit_status = stdout.channel.recv_exit_status()
            
            yield "─" * 50
            
            if exit_status == 0:
                yield f"✅ Command completed successfully (exit code: {exit_status})"
            else:
                # Read stderr
                err_output = stderr.read().decode().strip()
                if err_output:
                    yield f"⚠️ Stderr: {err_output}"
                yield f"❌ Command failed (exit code: {exit_status})"
                
        except paramiko.AuthenticationException:
            yield "❌ Authentication Failed"
        except paramiko.SSHException as e:
            yield f"❌ SSH Error: {str(e)}"
        except Exception as e:
            yield f"❌ Execution Error: {str(e)}"
        finally:
            if client:
                client.close()
                yield "🔌 Connection closed"

    @staticmethod
    async def upload_and_execute(
        hostname: str,
        username: str,
        private_key_str: str,
        local_path: str,
        port: int = 22
    ) -> AsyncGenerator[str, None]:
        """
        Combined operation: Upload file and execute it.
        Designed for Python scripts.
        """
        import os
        
        filename = os.path.basename(local_path)
        remote_path = f"/tmp/{filename}"
        
        yield f"📁 Preparing to upload: {filename}"
        
        # Step 1: Upload
        success, message = await SSHManager.upload_file(
            hostname=hostname,
            username=username,
            private_key_str=private_key_str,
            local_path=local_path,
            remote_path=remote_path,
            port=port
        )
        
        if not success:
            yield f"❌ Upload failed: {message}"
            return
        
        yield f"✅ {message}"
        yield f"📍 Remote path: {remote_path}"
        
        # Step 2: Execute
        command = f"python3 {remote_path}"
        
        async for line in SSHManager.execute_command(
            hostname=hostname,
            username=username,
            private_key_str=private_key_str,
            command=command,
            port=port
        ):
            yield line
        
        # Step 3: Cleanup (optional)
        yield f"🧹 Cleaning up remote file..."
        try:
            client, pkey = SSHManager._create_client_and_key(private_key_str)
            client.connect(hostname=hostname, port=port, username=username, pkey=pkey, timeout=5)
            stdin, stdout, stderr = client.exec_command(f"rm -f {remote_path}")
            stdout.channel.recv_exit_status()
            client.close()
            yield f"✅ Cleanup complete"
        except Exception as e:
            yield f"⚠️ Cleanup warning: {str(e)}"

    @staticmethod
    def save_key(user_id: str, key_name: str, private_key: str, public_key: str = ""):
        """
        Persists the SSH key to Supabase.
        TODO: Encrypt private_key before saving! (For MVP saving raw - WARNING)
        """
        db = get_db()
        if not db:
            raise Exception("Database unavailable")
            
        try:
            db.table("ssh_keys").insert({
                "user_id": user_id,
                "key_name": key_name,
                "private_key_enc": private_key,
                "public_key": public_key
            }).execute()
            logger.info(f"SSH Key '{key_name}' saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save key: {e}")
            raise e
