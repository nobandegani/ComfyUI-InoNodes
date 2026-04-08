# CLAUDE.md — comfyui_ino_nodes

## Project Overview

Custom node package for ComfyUI (v2.0.4) providing 131 nodes across 18 categories. Published by Inoland.

- **Package**: `comfyui_ino_nodes`
- **Python**: >= 3.10
- **Conda env**: `comfyui` — run Python commands with `conda run -n comfyui`
- **Entry point**: `__init__.py` (aggregates all nodes via `NODE_CLASS_MAPPINGS`)
- **Tests**: `conda run -n comfyui pytest` (from src/comfyui_ino_nodes)
- **Dependencies**: inopyutils, openai, aiohttp, numpy, Pillow, torch, huggingface_hub, hf_xet

## Architecture

All nodes use **ComfyUI V3 schema** (`io.ComfyNode` with `define_schema` + `execute` classmethod).

```
__init__.py                          # Root — registers all nodes + basic auth middleware + log_capture
src/comfyui_ino_nodes/
├── node_helper.py                   # Shared utilities (resolve_comfy_path, PARENT_FOLDER_OPTIONS, load_image, load_images_from_folder, LogCapture, etc.)
├── init_helper.py                   # Initialization utilities
├── basic_auth.py                    # HTTP Basic Auth middleware (1 node)
├── sync_assets.py                   # Asset synchronization
├── class_helpers/                   # Feature modules
│   ├── file_helper.py              # 13 nodes — InoFileHelper (zip, unzip, copy, remove, count, validate, dedup, etc.)
│   ├── media_helper.py             # 1 node — FFmpeg video conversion
│   ├── http_helper.py              # 1 node — REST client (GET/POST/PUT/DELETE/PATCH)
│   ├── json_helper.py              # 3 nodes — JSON field manipulation and save
│   ├── openai_helper.py            # 2 nodes — OpenAI API (responses + chat completions)
│   └── runpod_helper.py            # 1 node — Runpod serverless vLLM inference (with polling/retry)
├── node_helpers/                    # Data type nodes
│   ├── bool_helper.py              # 4 nodes — Boolean ops
│   ├── int_helper.py               # 4 nodes — Integer ops
│   ├── float_helper.py             # 2 nodes — Float ops
│   ├── string_helper.py            # 13 nodes — String manipulation + save text
│   ├── image_helper.py             # 14 nodes — Image load, save, resize, crop, batch, base64, megapixel resolution
│   ├── video_helper.py             # 1 node — Video preview
│   ├── time_helper.py              # 4 nodes — DateTime formatting and duration
│   ├── path_helper.py              # 2 nodes — Path utilities
│   └── cast_helper.py             # 7 nodes — Type casting (Any → String/Int/Model/Clip/Vae/ControlNet/etc.)
├── s3_helper/                       # S3 cloud storage (16 nodes)
│   ├── s3_helper.py                # S3Helper class + InoS3Config node
│   ├── s3_download_*.py            # Download: file, folder, image, audio
│   ├── s3_upload_*.py              # Upload: file, folder, image, audio, video, string
│   ├── s3_sync_folder_node.py      # Bidirectional sync
│   ├── s3_verify_file_node.py      # File verification
│   └── s3_get_download_url.py      # Presigned URL generation
├── utils/extra_nodes.py            # 9 nodes — Relay, switches, delay, logging, noise, length
├── workflow_helpers/                # Complex workflow nodes
│   ├── download_model_helper.py    # 13 nodes — Download from S3/HF/Civitai/HTTP
│   ├── load_model_helper.py        # 9 nodes — Load VAE/CLIP/ControlNet/Diffusion/LoRA
│   ├── lora_helper.py              # 1 node — Load multiple LoRAs
│   ├── prompt_helper.py            # 1 node — Random character prompt generation
│   └── sampler_helper.py           # 10 nodes — Model config, conditioning, sampler setup
├── data/                            # CSV/JSON configs for models, LoRAs, clips, VAEs
└── web/js/inonodes.js              # Frontend extension
```

## Node Categories (18 categories, 131 nodes)

| Category | Count | File(s) |
|---|---|---|
| InoBoolHelper | 4 | bool_helper.py |
| InoCastHelper | 7 | cast_helper.py |
| InoExtraNodes | 9 | extra_nodes.py |
| InoFileHelper | 13 | file_helper.py |
| InoFloatHelper | 2 | float_helper.py |
| InoHttpHelper | 1 | http_helper.py |
| InoImageHelper | 14 | image_helper.py |
| InoIntHelper | 4 | int_helper.py |
| InoJsonHelper | 3 | json_helper.py |
| InoMediaHelper | 1 | media_helper.py |
| InoModelHelper | 23 | download_model_helper.py, load_model_helper.py, lora_helper.py |
| InoOpenaiHelper | 2 | openai_helper.py |
| InoPathHelper | 2 | path_helper.py |
| InoRunpodHelper | 1 | runpod_helper.py |
| InoS3Helper | 16 | s3_helper/*.py |
| InoSamplerHelper | 10 | sampler_helper.py |
| InoStringHelper | 13 | string_helper.py |
| InoTimeHelper | 4 | time_helper.py |
| InoVideoHelper | 1 | video_helper.py |

## Coding Conventions

### V3 Node Pattern (ALL nodes use this)

```python
from comfy_api.latest import io

class MyNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MyNode",
            display_name="My Node",
            category="InoCategoryHelper",   # Always Ino{Category}Helper
            description="What this node does.",
            is_output_node=True,            # For side-effect nodes
            inputs=[...],
            outputs=[...],
        )

    @classmethod
    async def execute(cls, **kwargs) -> io.NodeOutput:
        return io.NodeOutput(...)
```

### Shared Utilities (node_helper.py)

- `PARENT_FOLDER_OPTIONS = ["input", "output", "temp"]` — combo options for folder selection
- `resolve_comfy_path(parent_folder, folder="", filename="")` → `(rel_path, abs_path)`
- `load_image(image_path)` → `(image_tensor, mask_tensor)` — matches native ComfyUI LoadImage behavior (EXIF, multi-frame, intermediate_dtype)
- `load_images_from_folder(parent_folder, folder, load_cap, skip_from_first)` → `(images_list, masks_list)`
- `log_capture` — LogCapture singleton, installed in `__init__.py`
- `ino_print_log(prefix, msg, e)` — debug logging (enabled via `COMFYUI_INO_DEBUG=1`)

### File/Save Node Convention

Nodes that deal with local files use:
- **Inputs**: `parent_folder` (combo: input/output/temp), `folder` (string), `filename` (string, if needed)
- **Outputs**: `success` (bool), `message` (string), `rel_path` (string), `abs_path` (string)

### S3 Nodes Convention

All S3 nodes use `parent_folder`/`folder` for local paths and output `success`, `message`, `rel_path`, `abs_path`.
- **Upload file/folder**: have `execute` trigger input and `delete_local` option
- **Upload media** (image/audio/video/string): save to local first, then upload to S3
- **Download media** (image/audio): download from S3 to local `parent_folder`/`folder`
- **Sync**: bidirectional sync between S3 and local folder
- **Verify**: compare local file against S3 (size, md5, sha256)

### Result Handling

- Use `ino_ok()` / `ino_err()` / `ino_is_err()` from inopyutils for dict results
- All async I/O operations use `await`
- V3 delegate calls use `.args` to access results: `result.args[0]` for first output

## Environment Variables

| Variable | Purpose |
|---|---|
| `COMFYUI_INO_DEBUG` | Enable debug logging (set to "1") |
| `COMFYUI_USERNAME` / `COMFYUI_PASSWORD` | Basic Auth for endpoints |
| `S3_ACCESS_KEY`, `S3_ACCESS_SECRET`, `S3_ENDPOINT_URL`, `S3_REGION_NAME`, `S3_BUCKET_NAME` | S3 credentials |
| `OPENAI_TOKEN` | OpenAI API key |
| `RUNPOD_API_KEY` | Runpod API key |
| `CIVITAI_TOKEN` | Civitai API token |

## Frontend

- `web/js/inonodes.js` — frontend extension for dynamic input UI
- `WEB_DIRECTORY = "./web"` registered in `__init__.py`
