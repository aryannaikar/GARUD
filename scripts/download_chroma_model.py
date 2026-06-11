import os
import tarfile
import requests
from pathlib import Path

def download_chroma_model():
    model_name = "all-MiniLM-L6-v2"
    url = f"https://chroma-onnx-models.s3.amazonaws.com/{model_name}/onnx.tar.gz"
    
    cache_dir = os.path.join(str(Path.home()), ".cache", "chroma", "onnx_models", model_name)
    os.makedirs(cache_dir, exist_ok=True)
    
    tar_path = os.path.join(cache_dir, "onnx.tar.gz")
    
    print(f"Starting robust download of {model_name}...")
    print(f"URL: {url}")
    print(f"Saving to: {tar_path}")
    
    # Download with streaming and a huge timeout so it never drops
    try:
        response = requests.get(url, stream=True, timeout=600)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(tar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Print progress every ~10MB
                    if downloaded % (1024 * 1024 * 5) < 8192:
                        print(f"Progress: {downloaded / (1024 * 1024):.1f} MB / {total_size / (1024 * 1024):.1f} MB")
        
        print("\nDownload complete! Extracting...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=cache_dir)
            
        print("Extraction complete! The AI model is fully installed and ready.")
        
    except Exception as e:
        print(f"Error during download: {e}")

if __name__ == "__main__":
    download_chroma_model()
