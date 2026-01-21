from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/demo")
async def get_demo_connection():
    """
    Returns pre-configured demo connection credentials for mock GPU node.
    This allows users to try the platform without manual SSH setup.
    """
    # Check if running in Docker environment
    demo_available = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_ENV") == "true"
    
    if not demo_available:
        return {
            "available": False,
            "message": "Demo server not available. Please run with docker-compose."
        }
    
    # Return hardcoded demo credentials
    # Note: Private key will be read from mock-gpu-node container
    return {
        "available": True,
        "name": "🎮 io-Guard Demo GPU Server",
        "hostname": "mock-gpu-node",
        "username": "root",
        "port": 22,
        "description": "Local Docker container simulating a real GPU server. " +
                      "This container runs in your Docker network and is accessible via SSH, " +
                      "just like a real io.net GPU node. Use it to test deployments safely.",
        "note": "✨ This is a real SSH server (not fake). Copy these credentials " +
               "and use them in the '+ Connect Remote Server' button to practice the workflow.",
        # Private key will be fetched separately for security
        "key_endpoint": "/v1/connections/demo/key"
    }

@router.get("/demo/key")
async def get_demo_private_key():
    """
    Returns the demo private key.
    In production, this would require authentication.
    For demo purposes, we return a pre-generated key.
    """
    import paramiko
    import io
    
    # Path for storing keys
    KEYS_DIR = "keys"
    PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "id_rsa_demo")
    PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "id_rsa_demo.pub")
    
    # Create keys directory if it doesn't exist
    if not os.path.exists(KEYS_DIR):
        os.makedirs(KEYS_DIR)
        
    # Check if keys exist, if not generate them
    if not os.path.exists(PRIVATE_KEY_PATH):
        try:
            # Generate new RSA key
            key = paramiko.RSAKey.generate(2048)
            
            # Save Private Key
            key.write_private_key_file(PRIVATE_KEY_PATH)
            
            # Save Public Key
            pub_key = f"{key.get_name()} {key.get_base64()} root@mock-node"
            with open(PUBLIC_KEY_PATH, "w") as f:
                f.write(pub_key)
                
            print(f"Generated new demo keys in {KEYS_DIR}")
            
        except Exception as e:
            return {
                "error": f"Failed to generate keys: {str(e)}",
                "available": False
            }
            
    # Read the private key
    try:
        with open(PRIVATE_KEY_PATH, "r") as f:
            demo_key = f.read()
    except Exception as e:
         return {
                "error": f"Failed to read key: {str(e)}",
                "available": False
            }

    return {
        "private_key": demo_key,
        "note": "This is a dynamically generated demo key. Ensure the public key is configured on the mock node."
    }
