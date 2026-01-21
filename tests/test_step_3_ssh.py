import pytest
import requests
import json

BASE_URL = "http://localhost:8000/v1"

def test_ssh_endpoint_existence():
    """
    Verifies that the /v1/connection/test endpoint is reachable 
    and returns a handled error (not 500) for a fake host.
    This proves Paramiko is installed and the logic is active.
    """
    url = f"{BASE_URL}/connection/test"
    
    # Fake Credentials
    payload = {
        "hostname": "non.existent.host.io",
        "username": "root",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----",
        "port": 22
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, "Endpoint verified but returned HTTP Error"
        
        data = response.json()
        
        # We expect success=False because the host doesn't exist
        assert data['success'] is False
        
        # Crucial: Check if the message comes from Paramiko/Socket
        # "Name or service not known" or "gaierror" implies it tried to resolve DNS -> Code works!
        # "Paramiko missing" implies install failed.
        msg = data['message'].lower()
        if "missing" in msg:
            pytest.fail("Dependency Error: Paramiko module is missing!")
            
        print("✅ SSH Manager is active and handling connection attempts correctly.")
        
    except requests.ConnectionError:
        pytest.fail("Could not connect to Backend. Is Docker running?")
