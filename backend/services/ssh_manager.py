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
    Supports: Private Key, Password, and Passphrase-protected keys.
    """

    @staticmethod
    def _create_client() -> paramiko.SSHClient:
        """Creates SSH client with auto-accept policy."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    @staticmethod
    def _parse_private_key(private_key_str: str, passphrase: Optional[str] = None) -> paramiko.PKey:
        """
        Parses private key string. Supports RSA, Ed25519, ECDSA.
        Optionally decrypts with passphrase.
        """
        pkey = None
        password = passphrase if passphrase else None
        
        # Try RSA
        try:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str), password=password)
            return pkey
        except paramiko.ssh_exception.PasswordRequiredException:
            raise ValueError("Key is encrypted. Please provide passphrase.")
        except Exception:
            pass
        
        # Try Ed25519
        try:
            pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(private_key_str), password=password)
            return pkey
        except paramiko.ssh_exception.PasswordRequiredException:
            raise ValueError("Key is encrypted. Please provide passphrase.")
        except Exception:
            pass
        
        # Try ECDSA
        try:
            pkey = paramiko.ECDSAKey.from_private_key(io.StringIO(private_key_str), password=password)
            return pkey
        except paramiko.ssh_exception.PasswordRequiredException:
            raise ValueError("Key is encrypted. Please provide passphrase.")
        except Exception:
            pass
        
        # Try DSA (legacy but still used)
        try:
            pkey = paramiko.DSSKey.from_private_key(io.StringIO(private_key_str), password=password)
            return pkey
        except Exception:
            pass
                
        raise ValueError("Invalid Private Key format. Supported: RSA, Ed25519, ECDSA, DSA (PEM format)")

    @staticmethod
    async def test_connection(
        hostname: str, 
        username: str, 
        port: int = 22,
        auth_type: str = "key",  # "key" or "password"
        private_key: Optional[str] = None,
        password: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Attempts to establish an SSH connection and run 'uptime'.
        
        Auth types:
        - "key": Private key authentication (with optional passphrase)
        - "password": Password authentication
        """
        client = SSHManager._create_client()
        
        try:
            logger.info(f"Connecting to {username}@{hostname}:{port} (auth: {auth_type})")
            
            if auth_type == "password":
                if not password:
                    return False, "Password is required for password authentication"
                
                client.connect(
                    hostname=hostname,
                    port=port,
                    username=username,
                    password=password,
                    timeout=10,
                    banner_timeout=10
                )
            else:  # key authentication
                if not private_key:
                    return False, "Private key is required for key authentication"
                
                pkey = SSHManager._parse_private_key(private_key, passphrase)
                
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
            auth_method = "password" if auth_type == "password" else "SSH key"
            return True, f"✅ Connected via {auth_method}! Uptime: {output}"

        except paramiko.AuthenticationException:
            return False, "Authentication Failed (Wrong credentials)"
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
        local_path: str,
        remote_path: str,
        port: int = 22,
        auth_type: str = "key",
        private_key: Optional[str] = None,
        password: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Uploads a file to remote server via SFTP."""
        client = SSHManager._create_client()
        
        try:
            logger.info(f"SFTP: Connecting to {hostname}:{port}...")
            
            if auth_type == "password":
                client.connect(hostname=hostname, port=port, username=username, 
                             password=password, timeout=15, banner_timeout=15)
            else:
                pkey = SSHManager._parse_private_key(private_key, passphrase)
                client.connect(hostname=hostname, port=port, username=username, 
                             pkey=pkey, timeout=15, banner_timeout=15)
            
            sftp = client.open_sftp()
            logger.info(f"SFTP: Uploading {local_path} -> {remote_path}")
            sftp.put(local_path, remote_path)
            
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
        command: str,
        port: int = 22,
        auth_type: str = "key",
        private_key: Optional[str] = None,
        password: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Executes a command on remote server and yields output lines."""
        client = SSHManager._create_client()
        
        try:
            yield f"🔌 Connecting to {hostname}:{port}..."
            
            if auth_type == "password":
                client.connect(hostname=hostname, port=port, username=username,
                             password=password, timeout=15, banner_timeout=15)
            else:
                pkey = SSHManager._parse_private_key(private_key, passphrase)
                client.connect(hostname=hostname, port=port, username=username,
                             pkey=pkey, timeout=15, banner_timeout=15)
            
            yield f"✅ Connected as {username}"
            yield f"🚀 Executing: {command}"
            yield "─" * 50
            
            stdin, stdout, stderr = client.exec_command(command, get_pty=True)
            
            for line in iter(stdout.readline, ""):
                if line:
                    yield line.rstrip()
                await asyncio.sleep(0.01)
            
            exit_status = stdout.channel.recv_exit_status()
            yield "─" * 50
            
            if exit_status == 0:
                yield f"✅ Command completed successfully (exit code: {exit_status})"
            else:
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
        local_path: str,
        port: int = 22,
        auth_type: str = "key",
        private_key: Optional[str] = None,
        password: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Combined operation: Upload file and execute it."""
        import os
        
        filename = os.path.basename(local_path)
        remote_path = f"/tmp/{filename}"
        
        yield f"📁 Preparing to upload: {filename}"
        
        success, message = await SSHManager.upload_file(
            hostname=hostname,
            username=username,
            local_path=local_path,
            remote_path=remote_path,
            port=port,
            auth_type=auth_type,
            private_key=private_key,
            password=password,
            passphrase=passphrase
        )
        
        if not success:
            yield f"❌ Upload failed: {message}"
            return
        
        yield f"✅ {message}"
        yield f"📍 Remote path: {remote_path}"
        
        command = f"python3 {remote_path}"
        
        async for line in SSHManager.execute_command(
            hostname=hostname,
            username=username,
            command=command,
            port=port,
            auth_type=auth_type,
            private_key=private_key,
            password=password,
            passphrase=passphrase
        ):
            yield line
        
        # Cleanup
        yield f"🧹 Cleaning up remote file..."
        try:
            client = SSHManager._create_client()
            if auth_type == "password":
                client.connect(hostname=hostname, port=port, username=username, password=password, timeout=5)
            else:
                pkey = SSHManager._parse_private_key(private_key, passphrase)
                client.connect(hostname=hostname, port=port, username=username, pkey=pkey, timeout=5)
            stdin, stdout, stderr = client.exec_command(f"rm -f {remote_path}")
            stdout.channel.recv_exit_status()
            client.close()
            yield f"✅ Cleanup complete"
        except Exception as e:
            yield f"⚠️ Cleanup warning: {str(e)}"

    @staticmethod
    def save_key(user_id: str, key_name: str, private_key: str, public_key: str = ""):
        """Persists the SSH key to Supabase."""
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
