import pytest
import requests
import os

BASE_URL = "http://localhost:8000"

def test_upload_flow():
    """
    Verifies the complete Upload -> Serve flow.
    1. Uploads a dummy python script.
    2. Checks if backend returns a valid URL.
    3. Downloads the file from that URL to verify accessibility.
    """
    upload_url = f"{BASE_URL}/v1/upload"
    
    # 1. Create Dummy Content
    filename = "test_gpu_job.py"
    file_content = b"print('Hello from GPU Node!')"
    
    files = {
        'file': (filename, file_content, 'text/x-python')
    }
    
    try:
        # 2. Upload
        print(f"\n📤 Uploading {filename} to {upload_url}...")
        response = requests.post(upload_url, files=files, timeout=5)
        
        assert response.status_code == 200, f"Upload Failed: {response.text}"
        data = response.json()
        
        print(f"✅ Upload Success! Response: {data}")
        
        download_url = data['url']
        assert "localhost" in download_url or "http" in download_url
        
        # 3. Verify Serving (Download back)
        print(f"📥 Verifying download from: {download_url}")
        
        # Note: distinct request to download_url
        # Ideally this URL is reachable from outside. 
        # Inside docker container 'localhost' refers to itself, so it should work if port 8000 is open.
        
        get_res = requests.get(download_url, timeout=5)
        assert get_res.status_code == 200, "Could not download the uploaded file"
        assert get_res.content == file_content, "Downloaded content integrity mismatch"
        
        print("🎉 Verification Complete: File cycle (Upload -> Serve -> Download) works!")
        
    except requests.ConnectionError:
        pytest.fail("Could not connect to Backend. Is Docker running?")
    except Exception as e:
        pytest.fail(f"Test Error: {e}")
