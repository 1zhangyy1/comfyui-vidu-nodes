print("Loading VIDU nodes...")

from .vidu_nodes import (
    Text2VideoNode,
    Image2VideoNode,
    Character2VideoNode,
    UpscaleVideoNode,
    VideoDownloaderNode,
    StartEnd2VideoNode
)

NODE_CLASS_MAPPINGS = {
    "Text2Video": Text2VideoNode,
    "Image2Video": Image2VideoNode,
    "Character2Video": Character2VideoNode,
    "UpscaleVideo": UpscaleVideoNode,
    "VideoDownloader": VideoDownloaderNode,
    "StartEnd2Video": StartEnd2VideoNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Text2Video": "Text to Video (VIDU)",
    "Image2Video": "Image to Video (VIDU)",
    "Character2Video": "Character to Video (VIDU)",
    "UpscaleVideo": "Upscale Video (VIDU)",
    "VideoDownloader": "Video Downloader (VIDU)",
    "StartEnd2Video": "Start-End to Video (VIDU)"
}

print("VIDU nodes loaded successfully!")

# 确保这些变量被正确导出
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'] 