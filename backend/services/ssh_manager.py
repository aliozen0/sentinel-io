import paramiko
import io
import logging
import asyncio
from typing import Tuple, Optional
from db.client import get_db

logger = logging.getLogger(__name__)

class SSHManager:
    """
    Handles secure connections to remote GPU nodes via Paramiko.
    """

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
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Handle Private Key format
            pkey = None
            try:
                pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str))
            except Exception:
                # Try generic key if RSA fails (e.g. Ed25519)
                try:
                    pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(private_key_str))
                except Exception:
                    # Final attempt: direct auth without pkey obj (sometimes works if format implies)
                    # or fail cleanly
                    pass
            
            if not pkey:
                 return False, "Invalid Private Key format. Ensure it is PEM (OpenSSH)."

            logger.info(f"Connecting to {username}@{hostname}:{port}...")
            
            # Paramiko connect is blocking, run in executor if high load, but for MVP direct is fine
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
        except Exception as e:
            return False, f"Connection Error: {str(e)}"
            
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
                "private_key_enc": private_key, # ALERT: Add Encryption here for v1.1
                "public_key": public_key
            }).execute()
            logger.info(f"SSH Key '{key_name}' saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save key: {e}")
            raise e
