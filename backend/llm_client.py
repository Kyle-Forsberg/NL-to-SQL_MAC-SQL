import requests
import json
from typing import Optional, Dict, Any


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama:13b"):
        self.base_url = base_url
        self.model = model
        
    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
            
        payload.update(kwargs)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.RequestException as e:
            print(f"Ollama API error: {e}")
            raise
            
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            models = response.json().get("models", [])
            return any(model["name"] == self.model for model in models)
        except:
            return False
