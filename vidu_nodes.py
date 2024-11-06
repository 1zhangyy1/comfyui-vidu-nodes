import requests
import json
import time
import os
from typing import Dict, List, Union

class ViduBaseNode:
    def __init__(self):
        self.api_base = "https://api.vidu.zone"
        self.token = None
    
    def _make_request(self, method, endpoint, data=None, headers=None, files=None):
        if not self.token:
            raise ValueError("API Token not configured")
            
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}"
            }
            
        url = f"{self.api_base}{endpoint}"
        response = requests.request(method, url, json=data, headers=headers, files=files)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"API request failed: {response.text}")
            
        return response.json()

    def _wait_for_completion(self, task_id, timeout=3600):
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("Task timed out")
                
            status = self._make_request("GET", f"/ent/v1/tasks/{task_id}/creations")
            if status["state"] == "success":
                return status
            elif status["state"] == "failed":
                raise Exception(f"Generation failed: {status['err_code']}")
                
            time.sleep(5)

class Text2VideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "duration": (["4", "8"],),
                "token": ("STRING", {"default": ""}),
            },
            "optional": {
                "style": (["general", "anime"],),
                "model": (["vidu-high-performance"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "enhance": ("BOOLEAN", {"default": True}),
                "moderation": ("BOOLEAN", {"default": False}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""})
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")  # video_url, cover_url, task_id
    RETURN_NAMES = ("video_url", "cover_url", "task_id")
    FUNCTION = "generate"
    CATEGORY = "VIDU"

    def generate(self, prompt, duration, token, style="general", model="vidu-high-performance", 
                seed=0, enhance=True, moderation=False, negative_prompt=""):
        self.token = token
        
        prompts = [{"type": "text", "content": prompt, "negative": False}]
        if negative_prompt:
            prompts.append({"type": "text", "content": negative_prompt, "negative": True})
        
        task_data = {
            "type": "text2video",
            "model": model,
            "style": style,
            "input": {
                "seed": seed,
                "enhance": enhance,
                "prompts": prompts
            },
            "output_params": {
                "sample_count": 1,
                "duration": int(duration)
            },
            "moderation": moderation
        }
        
        result = self._make_request("POST", "/ent/v1/tasks", task_data)
        task_id = result["id"]
        
        status = self._wait_for_completion(task_id)
        creation = status["creations"][0]
        
        return (creation["url"], creation["cover_url"], task_id)

class Image2VideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),  # ComfyUI image input
                "prompt": ("STRING", {"multiline": True}),
                "duration": (["4", "8"],),
                "token": ("STRING", {"default": ""})
            },
            "optional": {
                "model": (["vidu-high-performance"],),
                "enhance": ("BOOLEAN", {"default": True}),
                "moderation": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("video_url", "cover_url", "task_id")
    FUNCTION = "generate"
    CATEGORY = "VIDU"

    def generate(self, image, prompt, duration, token, model="vidu-high-performance", 
                enhance=True, moderation=False, seed=0):
        self.token = token
        
        # First upload the image
        image_uri = self._upload_image(image)
        
        task_data = {
            "type": "img2video",
            "model": model,
            "input": {
                "seed": seed,
                "enhance": enhance,
                "prompts": [
                    {"type": "text", "content": prompt},
                    {"type": "image", "content": image_uri}
                ]
            },
            "output_params": {
                "sample_count": 1,
                "duration": int(duration)
            },
            "moderation": moderation
        }
        
        result = self._make_request("POST", "/ent/v1/tasks", task_data)
        task_id = result["id"]
        
        status = self._wait_for_completion(task_id)
        creation = status["creations"][0]
        
        return (creation["url"], creation["cover_url"], task_id)

    def _upload_image(self, image) -> str:
        # Create upload request
        create_response = self._make_request("POST", "/tools/v1/files/uploads", 
                                           data={"scene": "vidu"})
        
        # Get upload URL and resource ID
        put_url = create_response["put_url"]
        resource_id = create_response["id"]
        
        # Convert tensor to PNG bytes
        import io
        from PIL import Image
        import torch

        # Convert tensor to PIL Image
        image = Image.fromarray((image[0] * 255).cpu().numpy().astype('uint8'))
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        
        # Upload using PUT request
        headers = {"Content-Type": "image/png"}
        response = requests.put(put_url, data=image_bytes, headers=headers)
        etag = response.headers.get("etag").strip('"')
        
        # Finish upload
        finish_response = self._make_request(
            "PUT",
            f"/tools/v1/files/uploads/{resource_id}/finish",
            data={"etag": etag}
        )
        
        return finish_response["uri"]

class Character2VideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "duration": (["4", "8"],),
                "token": ("STRING", {"default": ""})
            },
            "optional": {
                "model": (["vidu-high-performance"],),
                "enhance": ("BOOLEAN", {"default": True}),
                "moderation": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("video_url", "cover_url", "task_id")
    FUNCTION = "generate"
    CATEGORY = "VIDU"

    def generate(self, character_image, prompt, duration, token, model="vidu-high-performance", 
                enhance=True, moderation=False, seed=0):
        self.token = token
        
        # Upload character image
        image_uri = self._upload_image(character_image)
        
        task_data = {
            "type": "character2video",
            "model": model,
            "input": {
                "seed": seed,
                "enhance": enhance,
                "prompts": [
                    {"type": "text", "content": prompt},
                    {"type": "image", "content": image_uri}
                ]
            },
            "output_params": {
                "sample_count": 1,
                "duration": int(duration)
            },
            "moderation": moderation
        }
        
        result = self._make_request("POST", "/ent/v1/tasks", task_data)
        task_id = result["id"]
        
        status = self._wait_for_completion(task_id)
        creation = status["creations"][0]
        
        return (creation["url"], creation["cover_url"], task_id)

    _upload_image = Image2VideoNode._upload_image

class UpscaleVideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "creation_id": ("STRING",),
                "token": ("STRING", {"default": ""})
            },
            "optional": {
                "model": (["stable"],),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("video_url", "cover_url", "task_id")
    FUNCTION = "upscale"
    CATEGORY = "VIDU"

    def upscale(self, creation_id, token, model="stable"):
        self.token = token
        
        task_data = {
            "type": "upscale",
            "model": model,
            "input": {
                "creation_id": creation_id
            }
        }
        
        result = self._make_request("POST", "/ent/v1/tasks", task_data)
        task_id = result["id"]
        
        status = self._wait_for_completion(task_id)
        creation = status["creations"][0]
        
        return (creation["url"], creation["cover_url"], task_id)

class VideoDownloaderNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING",),
                "output_path": ("STRING", {"default": "outputs"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("local_path",)
    FUNCTION = "download"
    CATEGORY = "VIDU"

    def download(self, video_url, output_path):
        os.makedirs(output_path, exist_ok=True)
        filename = f"vidu_video_{int(time.time())}.mp4"
        local_path = os.path.join(output_path, filename)
        
        response = requests.get(video_url, stream=True)
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return (local_path,)