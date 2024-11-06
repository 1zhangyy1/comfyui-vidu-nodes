# ComfyUI VIDU 节点

这是一个用于 ComfyUI 的 VIDU API 集成节点包，支持文本生成视频、图像生成视频、角色生成视频以及视频超分等功能。

## 功能特点

该节点包提供以下功能：
- 文本生成视频 (Text to Video)
- 图像生成视频 (Image to Video)
- 角色生成视频 (Character to Video)
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

### 4. 视频超分 (Video Upscale)
提升视频分辨率。

参数说明：
- `creation_id`: 生成物 ID（必填）
- `token`: API Token（必填）
- `model`: 超分模型（默认 stable）

### 5. 视频下载器 (Video Downloader)
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

## 错误处理

如果遇到错误，请检查：
1. API Token 是否正确
2. 网络连接是否正常
3. 输入参数是否符合要求
4. 图片格式和大小是否符合限制

## 更新日志

[在这里添加版本更新信息]

## 支持与反馈

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 联系 VIDU 官方支持

## 许可证

[添加许可证信息]