# ComfyUI Ino Nodes

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![ComfyUI](https://img.shields.io/badge/ComfyUI-V3%20Schema-purple)
![Nodes](https://img.shields.io/badge/Nodes-125%2B-orange)

A comprehensive custom node package for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) delivering **125+ production-ready nodes** across **18 categories**. Built entirely on the modern **ComfyUI V3 schema**, Ino Nodes covers everything from file system operations and S3 cloud storage to image/video/audio processing, model management, OpenAI integration, and workflow utilities.

Whether you're building automated pipelines that download models from HuggingFace, upload results to S3, process images in batch, or chain LLM calls into your workflows — Ino Nodes provides the building blocks with consistent interfaces, proper error handling, and clean async execution throughout.

Every file-related node follows a unified pattern with `parent_folder` (input/output/temp) selection, `folder`, and `filename` inputs, outputting `success`, `message`, `rel_path`, and `abs_path` for predictable chaining. S3 upload nodes save to temp with unique filenames by default, media download nodes return native ComfyUI types (IMAGE, AUDIO, VIDEO), and all nodes include an `enabled` toggle and descriptive tooltips.

---

> **Important:** This package requires `inopyutils`. All S3 operations require S3 credentials configured via environment variables or the S3 Config node. OpenAI and Runpod nodes require their respective API keys. Basic Auth middleware is optional and only activates when `COMFYUI_USERNAME` and `COMFYUI_PASSWORD` are set.

---

## Installation

### ComfyUI-Manager (Recommended)

1. Install [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)
2. Search for **"ComfyUI Ino Nodes"** in the manager
3. Click install and restart ComfyUI

### Manual Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/nobandegani/ComfyUI-InoNodes.git
cd comfyui_ino_nodes
pip install -r requirements.txt
```

Restart ComfyUI after installation.

---

## Node Reference

### InoFileHelper (13 nodes)

File system operations with consistent `parent_folder`/`folder`/`filename` inputs and `success`/`message`/`rel_path`/`abs_path` outputs.

| Node | Description |
|---|---|
| **Ino Increment Batch Name** | Increments a batch name string (e.g., `Batch_00001` → `Batch_00002`) |
| **Ino Zip** | Zips a source folder into a zip file at the specified destination |
| **Ino Unzip** | Extracts a zip file to the specified destination folder |
| **Ino Remove File** | Removes a file from the filesystem |
| **Ino Remove Folder** | Removes a folder and all its contents recursively |
| **Ino Copy Files** | Copies files from one folder to another with optional renaming |
| **Ino Count Files** | Counts files in a folder, optionally recursively |
| **Ino Validate Media Files** | Validates and categorizes media files, separating valid from invalid |
| **Ino Remove Duplicate Files** | Removes duplicate files using SHA-256 hash comparison |
| **Ino Get Last File** | Returns the most recently modified file in a folder |
| **Ino Move Path** | Moves a file or folder from one location to another with optional overwrite |
| **Ino Get File Hash** | Computes the SHA-256 hash of a file |
| **Ino File To Base64** | Converts a file to a base64 data URI string with auto MIME detection |

### InoImageHelper (10 nodes)

Image loading, saving, resizing, cropping, and batch processing. Image loading uses EXIF rotation handling matching native ComfyUI behavior.

| Node | Description |
|---|---|
| **Ino Save Images** | Saves images to a specified folder with a filename prefix |
| **Ino Load Images From Folder** | Loads images from a folder with skip/cap options, returns images, masks, and count |
| **Ino Image Resize By Longer Side V1** | Resizes an image so the longer side matches the target size, preserving aspect ratio |
| **Ino Image Resize By Longer Side And Crop V2** | Resizes to fit target dimensions with optional cropping and position control |
| **Ino Image List To Batch** | Combines a list of images into a single batched tensor with resize or pad |
| **Ino Crop Image By Box** | Crops an image to a square region around a point with adjustable shift offsets |
| **Ino On Image List Completed** | Tracks image processing progress with a persistent counter stored in the folder |
| **Ino Image To Base64** | Converts an image to a base64-encoded data URL string |
| **Ino Images From Folder To Reference Latent** | Loads images, scales them, and encodes as reference latents for conditioning |
| **Ino Images To Reference Latent** | Encodes a batch of images as reference latents and applies them to conditioning |

### InoStringHelper (13 nodes)

String manipulation, formatting, and file saving.

| Node | Description |
|---|---|
| **Ino String Toggle Case** | Converts a string to upper or lower case |
| **Ino String Replace Placeholder** | Replaces all `{placeholder}` tokens in a string with a replacement value |
| **Ino String Replace** | Replaces all occurrences of a substring with another |
| **Ino String Strip Simple** | Removes all specified characters from a string |
| **Ino String To Alphabetic String** | Hashes a string and converts it to a fixed-length alphabetic-only string |
| **Ino Save Text** | Saves a text string to a file in the specified folder |
| **Ino String Concat** | Joins two strings with an optional separator |
| **Ino String Contains** | Checks if a string contains a substring, optionally case-insensitive |
| **Ino String Length** | Returns the character count of a string |
| **Ino String Trim** | Strips leading and/or trailing whitespace (both/left/right) |
| **Ino String Split** | Splits a string by a delimiter and returns the part at a given index |
| **Ino String Starts/Ends With** | Checks if a string starts or ends with a given substring |
| **Ino String Slice** | Extracts a substring by start and end index |

### InoS3Helper (16 nodes)

S3 cloud storage operations. Media uploads save to temp with unique filenames. Media downloads return native ComfyUI types.

| Node | Description |
|---|---|
| **Ino S3 Config** | Creates an S3 configuration string from credentials |
| **Ino S3 Download File** | Downloads a file from S3 to a local folder |
| **Ino S3 Download Folder** | Downloads an entire folder from S3 with concurrent downloads |
| **Ino S3 Download Image** | Downloads an image from S3 and returns it as IMAGE + MASK |
| **Ino S3 Download Audio** | Downloads an audio file from S3 and returns it as AUDIO |
| **Ino S3 Download Video** | Downloads a video file from S3 and returns it as VIDEO |
| **Ino S3 Download String** | Downloads a text file from S3 and returns its content as a string |
| **Ino S3 Upload File** | Uploads a local file to S3 with optional local deletion |
| **Ino S3 Upload Folder** | Uploads an entire folder to S3 with concurrent uploads and verification |
| **Ino S3 Upload Image** | Saves a single image as PNG to temp then uploads to S3 |
| **Ino S3 Upload Audio** | Saves audio as MP3 to temp then uploads to S3 |
| **Ino S3 Upload Video** | Saves video to temp then uploads to S3 |
| **Ino S3 Upload String** | Saves a string as a file (txt/json/ini) to temp then uploads to S3 |
| **Ino S3 Sync Folder** | Syncs a local folder with S3 bidirectionally (upload or download) |
| **Ino S3 Verify File** | Verifies a local file exists in S3 and optionally checks integrity via hash |
| **Ino S3 Get Download URL** | Generates a presigned download URL for an S3 object |

### InoModelHelper (23 nodes)

Model downloading from multiple sources and loading into ComfyUI.

| Node | Description |
|---|---|
| **Ino Create Model File Config** | Creates a model download configuration from individual fields |
| **Ino Get Image Model Download Config** | Retrieves image model download config from CSV |
| **Ino Get Video Model Download Config** | Retrieves video model download config from CSV |
| **Ino Get Vae Download Config** | Retrieves VAE model download config from CSV |
| **Ino Get Clip Download Config** | Retrieves CLIP model download config from CSV |
| **Ino Get Controlnet Download Config** | Retrieves ControlNet model download config from CSV |
| **Ino Get Lora Download Config** | Retrieves LoRA model download config from CSV |
| **Ino Http Download Model** | Downloads a model file from an HTTP URL |
| **Ino S3 Download Model** | Downloads a model file from S3 |
| **Ino Hugging Face Download Model** | Downloads a single model file from HuggingFace |
| **Ino Hugging Face Download Repo** | Downloads an entire repository from HuggingFace |
| **Ino Civitai Download Model** | Downloads a model file from Civitai |
| **Ino Handle Download Model** | Delegates download to the appropriate handler based on config |
| **Ino Load VAE Model** | Loads a VAE model from a file path |
| **Ino Load Controlnet Model** | Loads a ControlNet model from a file path |
| **Ino Load Clip Model** | Loads a CLIP model from a file path |
| **Ino Load Diffusion Model** | Loads a diffusion/UNET model from a file path |
| **Ino Load Lora Clip Model** | Loads a LoRA and applies it to both model and CLIP |
| **Ino Load Lora Model** | Loads a LoRA and applies it to the model only |
| **Ino Handle Load Model** | Generic model loader by type |
| **Ino Handle Download And Load Model** | Downloads and loads a model in a single operation |
| **Ino Get Model Path As String** | Returns the absolute path to a model directory for a given type |
| **Ino Load Multiple Lora** | Loads up to 5 LoRAs and applies them sequentially to model and CLIP |

### InoSamplerHelper (11 nodes)

Model configuration, conditioning, and sampler setup for generation workflows.

| Node | Description |
|---|---|
| **Ino Random Noise** | Generates random noise with selectable 32-bit or 64-bit seed precision |
| **Ino Get Model Config** | Retrieves a model configuration by name or ID from JSON |
| **Ino Get Lora Config** | Retrieves a LoRA configuration by name or ID from JSON |
| **Ino Create Lora Config** | Creates a LoRA configuration JSON from individual fields |
| **Ino Show Model Config** | Parses a model config JSON and outputs all individual fields |
| **Ino Update Model Config** | Overrides specific fields in a model config, unset values unchanged |
| **Ino Show Lora Config** | Parses a LoRA config JSON and outputs all individual fields |
| **Ino Load Sampler Models** | Downloads and loads UNET, CLIP, VAE and up to 4 LoRAs from config |
| **Ino Get Sampler Config** | Builds guider, sampler, and sigmas from a model config |
| **Ino Get Conditioning** | Encodes positive/negative conditioning with optional Flux encoder and guidance |
| **Ino Get Model Download Config** | Extracts individual download configs (UNET, CLIP1, CLIP2, VAE) from a model config |

### InoExtraNodes (8 nodes)

Workflow control, logic, and debugging utilities.

| Node | Description |
|---|---|
| **Ino Relay** | Passes through two values of any type, useful for controlling execution order |
| **Ino Any Equal** | Compares two values of the same type for equality |
| **Ino Delay Async** | Delays execution for a specified number of seconds |
| **Ino Print Log** | Prints a log message to the console and passes through the relay value |
| **Ino Switch On Bool** | Routes one of two inputs based on a boolean switch with lazy evaluation |
| **Ino Switch On Int** | Routes one of up to 10 inputs based on an integer index |
| **Ino Length** | Returns the length of a list or tuple input |
| **Ino Terminal Log** | Captures and returns the last N lines from terminal stdout |

### InoCastHelper (6 nodes)

Type casting from any type to specific ComfyUI types.

| Node | Description |
|---|---|
| **Ino Cast Any To String** | Casts any input value to a string |
| **Ino Cast Any To Int** | Casts any input value to an integer |
| **Ino Cast Any To Model** | Casts any input to a MODEL type |
| **Ino Cast Any To Clip** | Casts any input to a CLIP type |
| **Ino Cast Any To Vae** | Casts any input to a VAE type |
| **Ino Cast Any To Controlnet** | Casts any input to a CONTROL_NET type |

### InoBoolHelper (4 nodes)

Boolean logic operations.

| Node | Description |
|---|---|
| **Ino Boolean Equal** | Checks if two boolean values are equal |
| **Ino Not Boolean** | Negates a boolean value (NOT operation) |
| **Ino Bool To Switch** | Converts a boolean to an integer: 2 for true, 1 for false, -1 when disabled |
| **Ino Condition Boolean** | Performs AND or OR operation on two boolean values |

### InoIntHelper (4 nodes)

Integer operations and conversions.

| Node | Description |
|---|---|
| **Ino Random Int In Range** | Generates a random integer within a range with optional zero-padded string |
| **Ino Int To String** | Converts an integer to a string |
| **Ino Int To Float** | Converts an integer to a float |
| **Ino Compare Int** | Compares two integer values using a selected operator (=, <, >, <=, >=, <>) |

### InoTimeHelper (4 nodes)

Date and time formatting and calculations.

| Node | Description |
|---|---|
| **Ino DateTime Simple** | Returns the current UTC date and time as ISO or simple format string |
| **Ino DateTime Custom** | Returns a customizable datetime string with selectable components and separators |
| **Ino DateTime Duration** | Calculates the duration between two ISO datetime strings |
| **Ino DateTime Base64** | Returns the current UTC datetime encoded as a base64 string, unique per execution |

### InoJsonHelper (3 nodes)

JSON manipulation and persistence.

| Node | Description |
|---|---|
| **Ino Json Set Field** | Sets a field in a JSON string and returns the updated JSON |
| **Ino Json Get Field** | Gets a field value from a JSON string by field name |
| **Ino Save Json** | Saves a JSON string to a file in the specified folder |

### InoFloatHelper (2 nodes)

Float operations and conversions.

| Node | Description |
|---|---|
| **Ino Float To Int** | Converts a float to an integer using round, floor, or ceil |
| **Ino Compare Float** | Compares two float values using a selected operator |

### InoPathHelper (2 nodes)

ComfyUI path utilities.

| Node | Description |
|---|---|
| **Ino Get Comfy Path** | Returns the absolute path to a ComfyUI directory (input, output, or temp) |
| **Ino Get Lora Path Name Trigger Word** | Extracts the LoRA ID, name, and trigger word from a file path |

### InoOpenaiHelper (2 nodes)

OpenAI API integration.

| Node | Description |
|---|---|
| **Ino Openai Responses** | Sends a text or image prompt to OpenAI Responses API |
| **Ino Openai Chat Completions** | Sends a chat completion request to any OpenAI-compatible API |

### InoHttpHelper (1 node)

General-purpose HTTP client.

| Node | Description |
|---|---|
| **Ino Http Call** | Makes an HTTP request (GET/POST/PUT/DELETE/PATCH) and returns the response |

### InoMediaHelper (1 node)

Media format conversion.

| Node | Description |
|---|---|
| **Ino Convert Video To MP4** | Converts video files to MP4 via FFmpeg with optional FPS and resolution changes |

### InoRunpodHelper (1 node)

Runpod serverless inference.

| Node | Description |
|---|---|
| **Ino Vllm Run Sync** | Runs a synchronous vLLM inference request on Runpod serverless |

### InoVideoHelper (1 node)

Video preview.

| Node | Description |
|---|---|
| **Ino Preview Video** | Saves a video to the temp directory for in-node preview |

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `COMFYUI_INO_DEBUG` | No | Enable debug logging (set to `1`) |
| `COMFYUI_USERNAME` | No | Basic Auth username (enables auth when set with password) |
| `COMFYUI_PASSWORD` | No | Basic Auth password |
| `S3_ACCESS_KEY` | For S3 | S3 access key ID |
| `S3_ACCESS_SECRET` | For S3 | S3 secret access key |
| `S3_ENDPOINT_URL` | For S3 | S3 endpoint URL |
| `S3_REGION_NAME` | For S3 | S3 region |
| `S3_BUCKET_NAME` | For S3 | S3 bucket name |
| `OPENAI_TOKEN` | For OpenAI | OpenAI API key |
| `RUNPOD_API_KEY` | For Runpod | Runpod API key |
| `CIVITAI_TOKEN` | For Civitai | Civitai download token |

## Dependencies

| Package | Purpose |
|---|---|
| `inopyutils` | Core utility functions (file, S3, HTTP, JSON helpers) |
| `openai` | OpenAI API client |
| `aiohttp` | Async HTTP client and server middleware |
| `numpy` | Array operations |
| `Pillow` | Image processing |
| `torch` | Tensor operations |
| `huggingface_hub` | HuggingFace model downloads |
| `hf_xet` | HuggingFace extended transport |

## Project Info

| | |
|---|---|
| **Version** | 2.0.5 |
| **Python** | >= 3.10 |
| **ComfyUI** | v0.18.1+ |
| **Schema** | V3 (all nodes) |
| **License** | MIT |
| **Publisher** | [Inoland](https://inoland.net) |
| **Contact** | contact@inoland.net |
| **Repository** | [github.com/nobandegani/ComfyUI-InoNodes](https://github.com/nobandegani/ComfyUI-InoNodes) |
| **Registry** | [comfyregistry.org](https://comfyregistry.org) |

---

For issues and feature requests: [GitHub Issues](https://github.com/nobandegani/ComfyUI-InoNodes/issues)
