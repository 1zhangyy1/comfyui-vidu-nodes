# ComfyUI VIDU Nodes

A ComfyUI custom node extension that integrates VIDU API for video generation capabilities.

## Features

- Text to Video Generation
- Image to Video Generation
- Character to Video Generation
- Video Upscaling
- Video Downloading
- Full parameter control for all VIDU API features

## Installation

1. Clone this repository into your ComfyUI custom_nodes directory: 
bash
cd custom_nodes
git clone https://github.com/1zhangyy1/comfyui-vidu-nodes.git

2. Install the required dependencies:
```bash
pip install -r custom_nodes/comfyui-vidu-nodes/requirements.txt
```

3. Restart ComfyUI

## Usage

### API Token
You need a VIDU API token to use these nodes. You can provide the token in each node's configuration.

### Available Nodes

1. **Text to Video (VIDU)**
   - Generate videos from text prompts
   - Support for styles (general/anime)
   - Negative prompt support
   - Seed control

2. **Image to Video (VIDU)**
   - Convert static images to videos
   - Prompt guidance
   - Direct ComfyUI image input support

3. **Character to Video (VIDU)**
   - Animate character images
   - Specialized for character animation

4. **Upscale Video (VIDU)**
   - Enhance video resolution
   - Multiple model support

5. **Video Downloader (VIDU)**
   - Download generated videos
   - Custom output path support

## Parameters

Each node supports various parameters for fine-tuned control:

- Duration (4 or 8 seconds)
- Model selection
- Enhancement options
- Moderation settings
- Seed control
- And more...

## Examples

(Add workflow examples here)

## License

MIT License

## Credits

This extension integrates with the VIDU API service.