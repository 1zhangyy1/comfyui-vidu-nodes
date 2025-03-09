# ComfyUI VIDU 节点

这是一个用于 ComfyUI 的 VIDU API 集成节点包，支持文本生成视频、图像生成视频、角色生成视频以及视频超分等功能。

## 功能特点

该节点包提供以下功能：
- 文本生成视频 (Text to Video)
- 图像生成视频 (Image to Video)
- 角色生成视频 (Character to Video)
- 首尾帧生成视频 (Start-End to Video)
- 视频超分 (Video Upscale)
- 视频下载器 (Video Downloader)

## 安装方法

1. 进入 ComfyUI 的 `custom_nodes` 目录
2. 克隆本仓库：
```bash
git clone https://github.com/1zhangyy1/comfyui-vidu-nodes
```

## 使用前准备

使用前需要准备 VIDU API Token。请联系 VIDU 官方获取授权 Token。

## 节点说明

### 1. 文本生成视频 (Text to Video)
将文本描述转换为视频。

参数说明：
- `prompt`: 文本描述（必填）
- `duration`: 视频时长，支持 4 秒或 8 秒
- `token`: API Token（必填）
- `style`: 风格选择（general/anime）
- `model`: 模型选择（默认 vidu-high-performance）
- `seed`: 随机种子（可选）
- `enhance`: 是否启用提示词增强（默认开启）
- `moderation`: 是否开启审核（默认关闭）
- `negative_prompt`: 反向提示词（可选）

### 2. 图像生成视频 (Image to Video)
将静态图像转换为动态视频。

参数说明：
- `image`: 输入图像（必填）
- `prompt`: 文本描述（必填）
- `duration`: 视频时长
- `token`: API Token（必填）
- `model`: 模型选择
- `enhance`: 提示词增强
- `moderation`: 审核开关
- `seed`: 随机种子

### 3. 角色生成视频 (Character to Video)
基于角色图像生成视频。

参数说明：
- `character_image`: 角色图像（必填）
- `prompt`: 文本描述（必填）
- `duration`: 视频时长
- `token`: API Token（必填）
- 其他参数同上

### 4. 首尾帧生成视频 (Start-End to Video)
通过提供起始帧和结束帧，生成从一帧到另一帧的平滑过渡视频。

参数说明：
- `start_frame`: 起始帧图像（必填）
- `end_frame`: 结束帧图像（必填）
- `prompt`: 文本描述（必填）
- `token`: API Token（必填）
- `model`: 模型选择（vidu1.5/vidu2.0）
- `resolution`: 分辨率（360p/720p/1080p）
- `duration`: 视频时长（默认4秒，vidu2.0仅支持4秒）
- `seed`: 随机种子
- `movement_amplitude`: 运动幅度（auto/small/medium/large）
- `callback_url`: 回调URL（可选）

### 5. 视频超分 (Video Upscale)
提升视频分辨率。

参数说明：
- `creation_id`: 生成物 ID（必填）
- `token`: API Token（必填）
- `model`: 超分模型（默认 stable）

### 6. 视频下载器 (Video Downloader)
下载生成的视频到本地。

参数说明：
- `video_url`: 视频 URL（必填）
- `output_path`: 输出路径（默认为 outputs）

## 使用限制

- 图片格式仅支持 JPG 和 PNG
- 图片大小需要小于 50MB
- 图片长宽比需要小于 1:4 或 4:1
- Character to Video 任务的图片尺寸不能小于 128*128
- Character to Video 任务的图片比例需要小于 1:16 或 16:1
- 视频生成数量目前仅支持 1 个
- 视频时长目前支持 4 秒和 8 秒两种选项

## 注意事项

1. 请确保 API Token 的安全性，不要泄露给他人
2. 生成的视频链接有效期为 1 小时
3. 建议使用视频下载器节点及时保存重要的生成结果
4. 使用 Character to Video 功能时请注意图片尺寸要求
5. 所有节点现已支持Vidu API v2版本，确保您的Token具有v2 API的访问权限
6. 使用Start-End to Video功能时，请注意起始帧和结束帧的宽高比应相似（比例在0.8到1.25之间）

## API v2特别说明

本插件使用Vidu API v2版本，相比v1版本有以下变化：
1. 支持新的首尾帧生成视频功能
2. 图片上传流程调整，使用`/tools/v2/files/uploads`接口
3. 视频生成接口统一为`/v2/vidu/tasks`
4. 图片上传支持的格式包括PNG、JPEG、JPG和WebP
5. 首尾帧生成视频功能的图片要求：
   - 只接受2张图片（起始帧和结束帧）
   - 起始帧和结束帧的宽高比应在0.8到1.25之间
   - 图片宽高比必须小于1:4或4:1
   - 图片大小不得超过10MB

## 错误处理

如果遇到错误，请检查：
1. API Token 是否正确
2. 网络连接是否正常
3. 输入参数是否符合要求
4. 图片格式和大小是否符合限制
5. 查看ComfyUI的控制台输出，所有Vidu节点都会输出详细的日志信息
   - 日志格式为：`[Vidu 节点名称] 消息内容`
   - 包含请求URL、参数和响应的详细信息
   - 记录所有API交互的状态变化和错误信息

### 常见错误与解决方案

1. **404 Not Found** - 通常表示API路径错误或Token无效
2. **JSON解析错误** - 检查Token是否正确，服务器返回的是否为有效JSON
3. **上传图片失败** - 检查图片格式、大小是否符合要求
4. **任务状态查询失败** - 检查网络连接，任务ID是否正确
5. **未能获取etag** - 图片上传过程中的问题，检查网络连接和图片格式

如果在控制台看到"[Vidu XXX] 发生错误"类型的消息，可以根据附带的错误说明进行排查。

## 更新日志

### 2024年3月9日
- 新增首尾帧生成视频(Start-End to Video)节点
- 更新所有节点以支持Vidu API v2版本
- 添加详细的日志记录和错误处理机制
- 修复了图片上传相关的问题
- 统一了所有节点的API基础URL格式
- 优化了错误信息显示，便于用户调试

[在这里添加更多版本更新信息]

## 支持与反馈

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 联系 VIDU 官方支持

## 许可证

[添加许可证信息]