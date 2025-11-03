from typing import Dict, Optional
import requests

class OllamaLLM:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.api_endpoint = f"{host}/api/generate"
        self.tags_endpoint = f"{host}/api/tags"
    
    def get_server_status(self) -> Dict:
        """Check Ollama server status and return available models"""
        try:
            response = requests.get(self.tags_endpoint)
            response.raise_for_status()
            return {
                "status": "online",
                "models": response.json().get("models", []),
                "host": self.host
            }
        except Exception as e:
            return {
                "status": "offline",
                "error": str(e),
                "host": self.host
            }
    
    def update_host(self, new_host: str) -> Dict:
        """Update Ollama server host"""
        self.host = new_host
        self.api_endpoint = f"{new_host}/api/generate"
        self.tags_endpoint = f"{new_host}/api/tags"
        return self.get_server_status()
    
    def test_generation(self, model: str = "mistral") -> Dict:
        """Run a test generation to verify Ollama setup"""
        try:
            test_prompt = "Write 'Hello, world!' in a creative way."
            status = self.get_server_status()
            if status["status"] != "online":
                return {
                    "success": False,
                    "error": "Ollama server is not running",
                    "details": "Please start the server using 'ollama serve'"
                }
            
            if not self.check_and_pull_model(model):
                return {
                    "success": False,
                    "error": f"Model {model} is not available",
                    "details": f"Please run 'ollama pull {model}'"
                }
            
            response = self.generate(test_prompt, model=model)
            return {
                "success": True,
                "prompt": test_prompt,
                "response": response,
                "model": model
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Test generation failed",
                "details": str(e)
            }

    def check_and_pull_model(self, model: str) -> bool:
        """Check if model exists and pull if not available"""
        try:
            # Check if model is available
            status = self.get_server_status()
            if status["status"] != "online":
                return False
                
            models = [m["name"] for m in status.get("models", [])]
            if model not in models:
                # Try to pull the model
                pull_endpoint = f"{self.host}/api/pull"
                response = requests.post(pull_endpoint, json={"name": model})
                response.raise_for_status()
                return True
            return True
        except Exception:
            return False

    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                model: str = "mistral") -> str:
        """
        Generate a response using Ollama LLM
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for role-based responses
            model: The Ollama model to use
            
        Returns:
            str: Generated response
        """
        try:
            # Check server status
            status = self.get_server_status()
            if status["status"] != "online":
                return "⚠️ Error: Ollama server is not running. Please start the Ollama server using 'ollama serve' command."
                
            # Check/pull model if needed
            if not self.check_and_pull_model(model):
                return f"⚠️ Error: Model '{model}' is not available. Please run 'ollama pull {model}' to download it."
                
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            response = requests.post(self.api_endpoint, json=payload)
            response.raise_for_status()
            return response.json()["response"]
            
        except requests.exceptions.ConnectionError:
            return "⚠️ Error: Cannot connect to Ollama server. Please make sure Ollama is running using 'ollama serve'."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return f"⚠️ Error: Model '{model}' not found. Please run 'ollama pull {model}' to download it."
            return f"⚠️ Server error: {str(e)}"
        except Exception as e:
            return f"⚠️ Unexpected error: {str(e)}"