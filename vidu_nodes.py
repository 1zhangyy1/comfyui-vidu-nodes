import requests
import json
import time
import os
from typing import Dict, List, Union

class ViduBaseNode:
    def __init__(self):
        self.api_base = None
        self.token = None
        self.node_name = self.__class__.__name__
    
    def log(self, message):
        """记录带有节点名称前缀的日志消息"""
        print(f"[Vidu {self.node_name}] {message}")
    
    def _make_request(self, method, endpoint, data=None, headers=None, files=None):
        if not self.token:
            self.log("错误: API Token未配置")
            raise ValueError("API Token未配置")
        if not self.api_base:
            self.log("错误: API基础URL未配置")
            raise ValueError("API基础URL未配置")
            
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}"
            }
        
        url = f"{self.api_base}{endpoint}"
        self.log(f"发送{method}请求到: {url}")
        
        if data:
            self.log(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.request(method, url, json=data, headers=headers, files=files)
            
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应内容: {response.text[:1000]}{'...' if len(response.text) > 1000 else ''}")
            
            if response.status_code not in [200, 201]:
                self.log(f"API请求失败: {response.text}")
                raise Exception(f"API请求失败: {response.text}")
            
            try:
                return response.json()
            except json.JSONDecodeError as e:
                self.log(f"JSON解析错误: {str(e)}")
                self.log(f"原始响应内容: {response.text}")
                raise Exception(f"无法解析API响应: {str(e)}")
                
        except requests.RequestException as e:
            self.log(f"请求异常: {str(e)}")
            raise Exception(f"请求失败: {str(e)}")

    def _wait_for_completion(self, task_id, timeout=3600):
        self.log(f"开始轮询任务状态, ID: {task_id}")
        start_time = time.time()
        
        # 使用正确的API路径
        query_path = f"/ent/v2/tasks/{task_id}/creations"
        
        while True:
            if time.time() - start_time > timeout:
                self.log(f"任务超时: {task_id}")
                raise TimeoutError(f"任务超时，超过了最大等待时间({timeout}秒)")
            
            self.log(f"查询任务状态: {task_id}")
            
            try:
                status = self._make_request("GET", query_path)
                
                self.log(f"当前任务状态: {status.get('state', '未知')}")
                
                # 处理所有可能的状态
                if status["state"] == "success":
                    self.log(f"任务完成成功: {json.dumps(status, indent=2, ensure_ascii=False)}")
                    return status
                elif status["state"] == "failed":
                    err_code = status.get('err_code', '未知错误')
                    self.log(f"任务失败: {err_code}")
                    raise Exception(f"生成失败: {err_code}")
                elif status["state"] in ["created", "queueing", "processing"]:
                    self.log(f"任务处理中: {status['state']}, 等待5秒后再次查询...")
                    time.sleep(5)
                else:
                    self.log(f"未知状态: {status['state']}")
                    raise Exception(f"未知任务状态: {status['state']}")
                    
            except Exception as e:
                if not isinstance(e, TimeoutError) and "任务处理中" not in str(e):
                    self.log(f"查询过程中出错: {str(e)}")
                raise

    def _upload_image(self, image):
        """
        上传图片到Vidu服务器并返回图片URI
        """
        self.log("开始上传图片...")
        
        try:
            # 1. 创建上传请求
            self.log("创建上传请求...")
            
            # 使用v2版本的API路径
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}"
            }
            
            url = f"{self.api_base}/tools/v2/files/uploads"  # v1改为v2
            self.log(f"上传创建请求：{url}")
            
            response = requests.post(url, json={"scene": "vidu"}, headers=headers)
            
            if response.status_code not in [200, 201]:
                self.log(f"创建上传请求失败: {response.status_code}, {response.text}")
                raise Exception(f"创建上传请求失败: {response.text}")
            
            create_response = response.json()
            
            # 2. 获取上传URL和资源ID
            put_url = create_response["put_url"]
            resource_id = create_response["id"]
            self.log(f"获取到上传URL和资源ID: {resource_id}")
            self.log(f"上传URL: {put_url}")
            
            # 3. 准备图片数据
            import io
            from PIL import Image
            
            # Convert tensor to PIL Image and then to bytes
            self.log("转换图片数据...")
            pil_image = Image.fromarray((image[0] * 255).cpu().numpy().astype('uint8'))
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()
            self.log(f"图片准备完成, 大小: {len(image_bytes)/1024:.2f} KB")
            
            # 4. 上传图片
            self.log(f"开始上传图片到: {put_url}")
            headers = {"Content-Type": "image/png"}
            response = requests.put(put_url, data=image_bytes, headers=headers)
            
            if response.status_code not in [200, 201]:
                self.log(f"上传图片失败: {response.status_code}, {response.text}")
                raise Exception(f"上传图片失败: {response.text}")
            
            self.log("图片上传成功")
            
            # 5. 获取etag (注意要去掉引号)
            etag = response.headers.get("etag", "").strip('"')
            if not etag:
                self.log("未能获取etag，响应头：" + str(response.headers))
                raise Exception("未能获取etag")
            
            self.log(f"获取到etag: {etag}")
            
            # 6. 完成上传
            self.log(f"完成上传过程: {resource_id}")
            
            # 使用v2版本的API路径
            finish_url = f"{self.api_base}/tools/v2/files/uploads/{resource_id}/finish"  # v1改为v2
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}"
            }
            
            self.log(f"上传完成请求: {finish_url}")
            response = requests.put(finish_url, json={"etag": etag}, headers=headers)
            
            if response.status_code not in [200, 201]:
                self.log(f"完成上传失败: {response.status_code}, {response.text}")
                raise Exception(f"完成上传失败: {response.text}")
            
            finish_response = response.json()
            
            uri = finish_response["uri"]
            self.log(f"上传完成, 获取到URI: {uri}")
            return uri
            
        except Exception as e:
            self.log(f"上传过程中出错: {str(e)}")
            raise Exception(f"上传图片失败: {str(e)}")

class Text2VideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "duration": (["4", "8"],),
                "token": ("STRING", {"default": ""}),
                "api_base": ("STRING", {"default": "https://api.vidu.cn"}),
                "model_version": (["1.5", "2.0"],),
                "resolution": (["512", "720p", "1080p"],),
            },
            "optional": {
                "style": (["general", "anime"],),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "enhance": ("BOOLEAN", {"default": True}),
                "moderation": ("BOOLEAN", {"default": True}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "aspect_ratio": (["16:9", "9:16", "1:1"],),
                "movement_amplitude": (["auto", "small", "medium", "large"],),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("video_url", "cover_url", "task_id")
    FUNCTION = "generate"
    CATEGORY = "VIDU"

    def generate(self, prompt, duration, token, api_base, model_version, resolution, style="general",
                seed=0, enhance=True, moderation=True, negative_prompt="", 
                aspect_ratio="16:9", movement_amplitude="auto"):
        try:
            self.token = token
            self.api_base = api_base
            
            self.log(f"开始文本生成视频 - 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            
            prompts = [{"type": "text", "content": prompt, "negative": False}]
            if negative_prompt:
                self.log(f"添加负面提示词: {negative_prompt[:50]}{'...' if len(negative_prompt) > 50 else ''}")
                prompts.append({"type": "text", "content": negative_prompt, "negative": True})
            
            task_data = {
                "model": f"vidu{model_version}",  # 将1.5转为vidu1.5格式
                "style": style,
                "prompt": prompt,
                "duration": int(duration),
                "seed": seed,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "movement_amplitude": movement_amplitude
            }
            
            self.log("创建文本生成视频任务...")
            # 修改API基础URL和路径
            self.api_base = "https://api.vidu.cn"
            result = self._make_request("POST", "/ent/v2/text2video", task_data)
            task_id = result["task_id"]  # 注意：返回值中是task_id而非id
            
            self.log(f"任务创建成功, ID: {task_id}")
            
            self.log(f"等待任务完成: {task_id}")
            status = self._wait_for_completion(task_id)
            
            if "creations" in status and len(status["creations"]) > 0:
                creation = status["creations"][0]
                self.log(f"任务完成, 获取到视频URL: {creation['url']}")
                return (creation["url"], creation["cover_url"], task_id)
            else:
                self.log("警告: 响应中未找到视频信息")
                return ("任务完成但未找到视频URL", "", task_id)
                
        except Exception as e:
            self.log(f"生成过程出错: {str(e)}")
            return (f"错误: {str(e)}", "", "error")

class Image2VideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "duration": (["4", "8"],),
                "token": ("STRING", {"default": ""}),
                "api_base": ("STRING", {"default": "https://api.vidu.cn"}),
                "model_version": (["1.5", "2.0"],),
                "resolution": (["512", "720p", "1080p"],),
            },
            "optional": {
                "enhance": ("BOOLEAN", {"default": True}),
                "moderation": ("BOOLEAN", {"default": True}),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "aspect_ratio": (["16:9", "9:16", "1:1"],),
                "movement_amplitude": (["auto", "small", "medium", "large"],),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("video_url", "cover_url", "task_id")
    FUNCTION = "generate"
    CATEGORY = "VIDU"

    def generate(self, image, prompt, duration, token, api_base, model_version, resolution,
                enhance=True, moderation=True, seed=0, aspect_ratio="16:9", 
                movement_amplitude="auto"):
        try:
            self.token = token
            self.api_base = api_base
            
            self.log(f"开始图像生成视频 - 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            
            # 上传图像
            self.log("上传输入图像...")
            image_uri = self._upload_image(image)
            self.log(f"图像上传成功: {image_uri}")
            
            # 构建请求参数，与API文档保持一致
            task_data = {
                "model": f"vidu{model_version}",  # 将1.5转为vidu1.5格式
                "images": [image_uri],  # 注意这里是数组
                "prompt": prompt,
                "duration": int(duration),
                "seed": seed,
                "resolution": resolution,
                "movement_amplitude": movement_amplitude
            }
            
            self.log("创建图像生成视频任务...")
            # 使用正确的API端点
            self.api_base = "https://api.vidu.cn"  # 确保使用正确的域名
            result = self._make_request("POST", "/ent/v2/img2video", task_data)
            task_id = result["task_id"]  # 使用task_id而不是id
            
            self.log(f"任务创建成功, ID: {task_id}")
            
            self.log(f"等待任务完成: {task_id}")
            status = self._wait_for_completion(task_id)
            
            # 处理结果
            if "creations" in status and len(status["creations"]) > 0:
                creation = status["creations"][0]
                self.log(f"任务完成, 获取到视频URL: {creation['url']}")
                return (creation["url"], creation["cover_url"], task_id)
            else:
                self.log("警告: 响应中未找到视频信息")
                return ("任务完成但未找到视频URL", "", task_id)
                
        except Exception as e:
            self.log(f"生成过程出错: {str(e)}")
            return (f"错误: {str(e)}", "", "error")

class Character2VideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "duration": (["4", "8"],),
                "token": ("STRING", {"default": ""}),
                "api_base": ("STRING", {"default": "https://api.vidu.cn"}),
                "model_version": (["1.5", "2.0"],),
                "resolution": (["512", "720p", "1080p"],),
            },
            "optional": {
                "enhance": ("BOOLEAN", {"default": True}),
                "moderation": ("BOOLEAN", {"default": True}),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "aspect_ratio": (["16:9", "9:16", "1:1"],),
                "movement_amplitude": (["auto", "small", "medium", "large"],),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("video_url", "cover_url", "task_id")
    FUNCTION = "generate"
    CATEGORY = "VIDU"

    def generate(self, character_image, prompt, duration, token, api_base, model_version, resolution,
                enhance=True, moderation=True, seed=0, aspect_ratio="16:9", 
                movement_amplitude="auto"):
        try:
            self.token = token
            self.api_base = api_base
            
            self.log(f"开始角色生成视频 - 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            
            # 上传角色图像
            self.log("上传角色图像...")
            image_uri = self._upload_image(character_image)
            self.log(f"角色图像上传成功: {image_uri}")
            
            # 构建请求参数，与API文档保持一致
            task_data = {
                "model": f"vidu{model_version}",
                "images": [image_uri],  # 参考图生成视频API接受1-3张图片
                "prompt": prompt,
                "duration": int(duration),
                "seed": seed,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "movement_amplitude": movement_amplitude
            }
            
            self.log("创建角色生成视频任务...")
            # 使用正确的API端点
            self.api_base = "https://api.vidu.cn"
            result = self._make_request("POST", "/ent/v2/reference2video", task_data)
            task_id = result["task_id"]
            
            self.log(f"任务创建成功, ID: {task_id}")
            
            self.log(f"等待任务完成: {task_id}")
            status = self._wait_for_completion(task_id)
            
            # 处理结果
            if "creations" in status and len(status["creations"]) > 0:
                creation = status["creations"][0]
                self.log(f"任务完成, 获取到视频URL: {creation['url']}")
                return (creation["url"], creation["cover_url"], task_id)
            else:
                self.log("警告: 响应中未找到视频信息")
                return ("任务完成但未找到视频URL", "", task_id)
                
        except Exception as e:
            self.log(f"生成过程出错: {str(e)}")
            return (f"错误: {str(e)}", "", "error")

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
        try:
            self.token = token
            self.api_base = "https://api.vidu.cn"
            
            self.log(f"开始视频超分 - 生成物ID: {creation_id}")
            
            task_data = {
                "model": model,
                "creation_id": creation_id
            }
            
            self.log("创建视频超分任务...")
            result = self._make_request("POST", "/ent/v2/upscale", task_data)
            task_id = result["task_id"]
            self.log(f"任务创建成功, ID: {task_id}")
            
            self.log(f"等待任务完成: {task_id}")
            status = self._wait_for_completion(task_id)
            
            if "creations" in status and len(status["creations"]) > 0:
                creation = status["creations"][0]
                self.log(f"任务完成, 获取到视频URL: {creation['url']}")
                return (creation["url"], creation["cover_url"], task_id)
            else:
                self.log("警告: 响应中未找到视频信息")
                return ("任务完成但未找到视频URL", "", task_id)
                
        except Exception as e:
            self.log(f"超分过程出错: {str(e)}")
            return (f"错误: {str(e)}", "", "error")

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
        try:
            self.log(f"开始下载视频: {video_url}")
            
            os.makedirs(output_path, exist_ok=True)
            filename = f"vidu_video_{int(time.time())}.mp4"
            local_path = os.path.join(output_path, filename)
            
            self.log(f"保存路径: {local_path}")
            
            response = requests.get(video_url, stream=True)
            if response.status_code != 200:
                self.log(f"下载请求失败: {response.status_code}, {response.text}")
                return (f"下载失败: HTTP {response.status_code}",)
            
            file_size = int(response.headers.get('content-length', 0))
            self.log(f"文件大小: {file_size/1024/1024:.2f} MB")
            
            with open(local_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if file_size > 0 and downloaded % (1024*1024) < 8192:  # 每1MB打印一次进度
                            percent = (downloaded / file_size) * 100
                            self.log(f"下载进度: {percent:.1f}% ({downloaded/1024/1024:.2f}/{file_size/1024/1024:.2f} MB)")
            
            self.log(f"视频下载完成: {local_path}")
            return (local_path,)
            
        except Exception as e:
            self.log(f"下载过程出错: {str(e)}")
            return (f"下载错误: {str(e)}",)

class StartEnd2VideoNode(ViduBaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "start_frame": ("IMAGE",),
                "end_frame": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True}),
                "token": ("STRING", {"default": ""}),
                "api_base": ("STRING", {"default": "https://api.vidu.cn"}),
                "model": (["vidu2.0", "vidu1.5"],),
                "resolution": (["360p", "720p", "1080p"],),
            },
            "optional": {
                "duration": (["4", "8"],),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "movement_amplitude": (["auto", "small", "medium", "large"],),
                "callback_url": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "task_id")
    FUNCTION = "generate"
    CATEGORY = "VIDU"

    def generate(self, start_frame, end_frame, prompt, token, api_base, model, resolution,
                duration="4", seed=0, movement_amplitude="auto", callback_url=""):
        try:
            self.token = token
            self.api_base = api_base
            
            self.log(f"开始首尾帧生成视频 - 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            
            # 上传起始帧和结束帧图片
            self.log("上传起始帧图像...")
            start_frame_uri = self._upload_image(start_frame)
            self.log(f"起始帧上传成功: {start_frame_uri}")
            
            self.log("上传结束帧图像...")
            end_frame_uri = self._upload_image(end_frame)
            self.log(f"结束帧上传成功: {end_frame_uri}")
            
            # 准备请求数据
            task_data = {
                "model": model,
                "images": [start_frame_uri, end_frame_uri],
                "prompt": prompt,
                "duration": int(duration),
                "seed": seed,
                "resolution": resolution,
                "movement_amplitude": movement_amplitude
            }
            
            # 如果设置了回调URL，添加到请求中
            if callback_url:
                task_data["callback_url"] = callback_url
                self.log(f"设置回调URL: {callback_url}")
            
            # 打印请求详情
            self.log(f"请求API: {self.api_base}/ent/v2/start-end2video")
            self.log(f"请求参数: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
            
            # 修改请求头格式以适应V2 API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}"
            }
            
            # 发送请求到V2 API
            url = f"{self.api_base}/ent/v2/start-end2video"
            response = requests.post(url, json=task_data, headers=headers)
            
            # 打印响应状态和内容
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应内容: {response.text}")
            
            if response.status_code not in [200, 201]:
                self.log(f"API请求失败: {response.text}")
                raise Exception(f"API请求失败: {response.text}")
            
            # 尝试解析JSON响应
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                self.log(f"JSON解析错误: {str(e)}")
                self.log(f"原始响应内容: {response.text}")
                raise Exception(f"无法解析API响应: {str(e)}")
            
            task_id = result.get("task_id")
            if not task_id:
                self.log(f"警告: 响应中未找到task_id: {result}")
                raise Exception(f"响应中未找到task_id: {result}")
            
            self.log(f"任务创建成功, ID: {task_id}")
            
            # V2 API可能有不同的状态检查机制，这里使用轮询方式等待任务完成
            video_url = self._wait_for_v2_completion(task_id)
            self.log(f"获取到视频URL: {video_url}")
            
            return (video_url, task_id)
            
        except Exception as e:
            self.log(f"首尾帧生成视频过程出错: {str(e)}")
            return (f"错误: {str(e)}", "error")

    def _wait_for_v2_completion(self, task_id, timeout=3600):
        """
        等待V2 API任务完成并返回视频URL
        """
        self.log(f"开始轮询首尾帧任务状态, ID: {task_id}")
        start_time = time.time()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}"
        }
        
        while True:
            if time.time() - start_time > timeout:
                self.log(f"任务超时: {task_id}")
                raise TimeoutError("任务超时，超过了最大等待时间")
                
            # 查询任务状态
            url = f"{self.api_base}/ent/v2/start-end2video/{task_id}"
            self.log(f"查询任务状态: {url}")
            
            try:
                response = requests.get(url, headers=headers)
                self.log(f"状态查询响应: {response.status_code}, {response.text}")
                
                if response.status_code not in [200, 201]:
                    self.log(f"查询任务状态失败: {response.text}")
                    raise Exception(f"任务状态查询失败: {response.text}")
                
                try:
                    status = response.json()
                except json.JSONDecodeError as e:
                    self.log(f"状态JSON解析错误: {str(e)}, 原始内容: {response.text}")
                    raise Exception(f"无法解析状态响应: {str(e)}")
                
                # 打印当前状态
                self.log(f"当前任务状态: {status.get('state', '未知')}")
                
                # 处理任务状态
                if status.get("state") == "success":
                    self.log(f"任务完成成功: {json.dumps(status, indent=2, ensure_ascii=False)}")
                    # 成功后获取视频URL
                    if "creations" in status and len(status["creations"]) > 0:
                        return status["creations"][0]["url"]
                    else:
                        self.log(f"警告: 响应中未找到视频URL: {status}")
                        raise Exception("响应中未找到视频URL")
                elif status.get("state") == "failed":
                    err_code = status.get("err_code", "未知错误")
                    self.log(f"任务失败: {err_code}")
                    raise Exception(f"生成失败: {err_code}")
                elif status.get("state") in ["created", "queueing", "processing"]:
                    self.log(f"任务处理中: {status.get('state')}, 等待5秒后再次查询...")
                    time.sleep(5)
                else:
                    self.log(f"未知状态: {status.get('state')}")
                    raise Exception(f"未知任务状态: {status.get('state')}")
                    
            except Exception as e:
                if not isinstance(e, TimeoutError) and "任务处理中" not in str(e):
                    self.log(f"查询过程中出错: {str(e)}")
                raise