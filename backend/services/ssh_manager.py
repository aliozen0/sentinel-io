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
        
        # Guard against None
        if not private_key_str:
            return None

        # Clean up key string
        private_key_str = private_key_str.strip()
        
        # Common classes to try
        key_classes = [
            (paramiko.RSAKey, "RSA"),
            (paramiko.Ed25519Key, "Ed25519"),
            (paramiko.ECDSAKey, "ECDSA"),
            (paramiko.DSSKey, "DSA")
        ]
        
        errors = []
        
        for k_class, name in key_classes:
            try:
                # Need to seek(0) if reusing config, but here we create new StringIO each time
                pkey = k_class.from_private_key(io.StringIO(private_key_str), password=password)
                return pkey
            except paramiko.ssh_exception.PasswordRequiredException:
                raise ValueError("Key is encrypted. Please provide passphrase.")
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
        
        # If all failed
        logger.error(f"SSH Key Parse Errors: {'; '.join(errors)}")
        raise ValueError(f"Invalid Private Key format. Tried RSA, Ed25519, ECDSA, DSA. Details: {errors[0] if errors else 'Unknown'}")

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
        
        command = f"python3 -u {remote_path}"
        
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
    async def upload_directory(
        hostname: str,
        username: str,
        local_dir: str,
        remote_dir: str,
        port: int = 22,
        auth_type: str = "key",
        private_key: Optional[str] = None,
        password: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Uploads entire directory to remote server via SFTP, maintaining structure."""
        import os
        
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
            
            sftp = client.open_sftp()
            
            # Create remote base directory
            try:
                sftp.mkdir(remote_dir)
                yield f"📁 Created remote directory: {remote_dir}"
            except IOError:
                yield f"📁 Remote directory exists: {remote_dir}"
            
            # Count files first
            file_count = sum(len(files) for _, _, files in os.walk(local_dir))
            yield f"📦 Uploading {file_count} files..."
            
            uploaded = 0
            
            # Walk and upload
            for root, dirs, files in os.walk(local_dir):
                rel_root = os.path.relpath(root, local_dir)
                if rel_root == ".":
                    remote_root = remote_dir
                else:
                    remote_root = f"{remote_dir}/{rel_root}".replace("\\", "/")
                
                # Create subdirectories
                for d in dirs:
                    remote_subdir = f"{remote_root}/{d}".replace("\\", "/")
                    try:
                        sftp.mkdir(remote_subdir)
                    except IOError:
                        pass  # Already exists
                
                # Upload files
                for f in files:
                    local_path = os.path.join(root, f)
                    remote_path = f"{remote_root}/{f}".replace("\\", "/")
                    sftp.put(local_path, remote_path)
                    uploaded += 1
                    
                    if uploaded % 5 == 0 or uploaded == file_count:
                        yield f"📤 Progress: {uploaded}/{file_count} files"
            
            sftp.close()
            yield f"✅ Directory uploaded successfully ({uploaded} files)"
            
        except paramiko.AuthenticationException:
            yield "❌ SFTP Authentication Failed"
        except paramiko.SSHException as e:
            yield f"❌ SFTP Error: {str(e)}"
        except Exception as e:
            yield f"❌ Upload Error: {str(e)}"
        finally:
            client.close()

    @staticmethod
    async def upload_project_and_execute(
        hostname: str,
        username: str,
        project_dir: str,
        entry_point: str,
        port: int = 22,
        auth_type: str = "key",
        private_key: Optional[str] = None,
        password: Optional[str] = None,
        passphrase: Optional[str] = None,
        install_requirements: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Uploads a project directory and executes the entry point script.
        Optionally installs requirements.txt first.
        """
        import os
        
        project_name = os.path.basename(project_dir)
        remote_project_dir = f"/tmp/{project_name}"
        
        yield f"🚀 Starting project deployment: {project_name}"
        yield f"📍 Remote path: {remote_project_dir}"
        yield "─" * 50
        
        # Upload directory
        async for line in SSHManager.upload_directory(
            hostname=hostname,
            username=username,
            local_dir=project_dir,
            remote_dir=remote_project_dir,
            port=port,
            auth_type=auth_type,
            private_key=private_key,
            password=password,
            passphrase=passphrase
        ):
            yield line
        
        # Check for requirements.txt and install if present
        requirements_path = os.path.join(project_dir, "requirements.txt")
        if install_requirements and os.path.exists(requirements_path):
            yield "─" * 50
            yield "📦 Installing requirements.txt..."
            
            install_cmd = f"cd {remote_project_dir} && pip install -r requirements.txt --quiet"
            
            async for line in SSHManager.execute_command(
                hostname=hostname,
                username=username,
                command=install_cmd,
                port=port,
                auth_type=auth_type,
                private_key=private_key,
                password=password,
                passphrase=passphrase
            ):
                yield line
        
        # Execute entry point
        yield "─" * 50
        yield f"▶️ Executing: {entry_point}"
        
        run_cmd = f"cd {remote_project_dir} && python3 -u {entry_point}"
        
        async for line in SSHManager.execute_command(
            hostname=hostname,
            username=username,
            command=run_cmd,
            port=port,
            auth_type=auth_type,
            private_key=private_key,
            password=password,
            passphrase=passphrase
        ):
            yield line
        
        # Cleanup
        yield "─" * 50
        yield f"🧹 Cleaning up remote project..."
        try:
            client = SSHManager._create_client()
            if auth_type == "password":
                client.connect(hostname=hostname, port=port, username=username, password=password, timeout=5)
            else:
                pkey = SSHManager._parse_private_key(private_key, passphrase)
                client.connect(hostname=hostname, port=port, username=username, pkey=pkey, timeout=5)
            stdin, stdout, stderr = client.exec_command(f"rm -rf {remote_project_dir}")
            stdout.channel.recv_exit_status()
            client.close()
            yield f"✅ Project cleanup complete"
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
