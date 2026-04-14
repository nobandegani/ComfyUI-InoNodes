from pathlib import Path
import os
import csv
import sys
import collections
import threading


class _StreamInterceptor:
    """Wraps a stream (stdout/stderr) and copies output to a shared buffer."""

    def __init__(self, original, buffer, lock):
        self._original = original
        self._buffer = buffer
        self._lock = lock

    @property
    def encoding(self):
        return getattr(self._original, "encoding", "utf-8")

    def write(self, text):
        if self._original:
            self._original.write(text)
        if text and text != "\n":
            with self._lock:
                for line in text.rstrip("\n").split("\n"):
                    self._buffer.append(line)

    def flush(self):
        if self._original:
            self._original.flush()

    def __getattr__(self, name):
        return getattr(self._original, name)


class LogCapture:
    """Captures terminal output (stdout + stderr) into a ring buffer."""

    def __init__(self, max_lines=10000):
        self._buffer = collections.deque(maxlen=max_lines)
        self._lock = threading.Lock()
        self._installed = False

    def install(self):
        if self._installed:
            return
        sys.stdout = _StreamInterceptor(sys.stdout, self._buffer, self._lock)
        sys.stderr = _StreamInterceptor(sys.stderr, self._buffer, self._lock)
        self._installed = True

    def get_lines(self, count):
        with self._lock:
            lines = list(self._buffer)
        return lines[-count:] if count < len(lines) else lines


log_capture = LogCapture()

# wildcard trick is taken from pythongossss's
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

any_type = AnyType("*")

_is_debug = os.getenv('COMFYUI_INO_DEBUG') == "1"
IS_DEBUG  = _is_debug
print(f"COMFYUI_INO_DEBUG: {_is_debug}")

def ino_print_log(prefix:str = "", msg:str="unknown", e = None):
    if IS_DEBUG:
        message = ""
        if prefix:
            message += f"[{prefix}]: "
        message += f"{msg}"
        if e:
            message += f" ->{e}"
        print(message)

MODEL_TYPES = (
    "audio_encoders",
    "checkpoints",
    "clip",
    "clip_vision",
    "controlnet",
    "detection",
    "DiffuEraser",
    "diffusers",
    "diffusion_models",
    "embeddings",
    "face_restore",
    "facerestore_models",
    "hyperswap",
    "Joy_caption",
    "llm",
    "loras",
    "insightface",
    "prompt_generator",
    "reswapper",
    "sam",
    "sam2",
    "sams",
    "style_models",
    "text_encoders",
    "transformers",
    "tts",
    "ultralytics",
    "unet",
    "upscale_models",
    "vae",
    "vibevoice",
    "wav2vec2",
)

UNET_WEIGHT_DTYPE= ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"]

CLIP_TYPE= ["stable_diffusion", "stable_cascade", "sd3", "stable_audio", "mochi", "ltxv", "pixart", "cosmos", "lumina2", "wan", "hidream", "chroma", "ace", "omnigen2", "qwen_image", "hunyuan_image", "flux2", "ovis"]

PARENT_FOLDER_OPTIONS = ["input", "output", "temp"]


def _load_csv_as_dict(is_config: bool, model_type: str) -> list:
    base_dir = Path(__file__).resolve().parent.parent.parent
    middle_dir = "configs" if is_config else "files"
    csv_path: Path = base_dir / "data" / middle_dir / f"{model_type}.csv"

    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return []

    with open(str(csv_path.resolve()), mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)

def get_list_from_csv(is_config: bool, model_type: str, return_only_names):
    csv_data = _load_csv_as_dict(is_config, model_type)
    data = []

    if return_only_names:
        for row in csv_data:
            data.append(row["name"])
    else:
        data = csv_data

    return data

def resolve_comfy_path(parent_folder: str, folder: str = "", filename: str = "") -> tuple:
    """Resolves parent_folder + folder + filename into (rel_path, abs_path)."""
    import folder_paths
    if parent_folder == "input":
        parent_path = folder_paths.get_input_directory()
    elif parent_folder == "output":
        parent_path = folder_paths.get_output_directory()
    else:
        parent_path = folder_paths.get_temp_directory()

    parts = []
    if folder:
        parts.append(folder)
    if filename:
        parts.append(filename)

    if parts:
        rel = str(Path(*parts))
        abs_path = str((Path(parent_path) / rel).resolve())
    else:
        rel = ""
        abs_path = str(Path(parent_path).resolve())
    return rel, abs_path


def load_image(image_path: str):
    """Loads a single image from path. Matches native ComfyUI LoadImage behavior:
    EXIF rotation, multi-frame support, alpha mask extraction, intermediate dtype.
    Returns (image_tensor, mask_tensor)."""
    import torch
    import numpy as np
    import node_helpers
    import comfy.model_management
    from PIL import Image, ImageOps, ImageSequence

    img = node_helpers.pillow(Image.open, image_path)

    output_images = []
    output_masks = []
    w, h = None, None

    dtype = comfy.model_management.intermediate_dtype()

    for i in ImageSequence.Iterator(img):
        i = node_helpers.pillow(ImageOps.exif_transpose, i)

        if i.mode == 'I':
            i = i.point(lambda i: i * (1 / 255))
        image = i.convert("RGB")

        if len(output_images) == 0:
            w = image.size[0]
            h = image.size[1]

        if image.size[0] != w or image.size[1] != h:
            continue

        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        elif i.mode == 'P' and 'transparency' in i.info:
            mask = np.array(i.convert('RGBA').getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
        output_images.append(image.to(dtype=dtype))
        output_masks.append(mask.unsqueeze(0).to(dtype=dtype))

        if img.format == "MPO":
            break

    if len(output_images) > 1:
        output_image = torch.cat(output_images, dim=0)
        output_mask = torch.cat(output_masks, dim=0)
    else:
        output_image = output_images[0]
        output_mask = output_masks[0]

    return output_image, output_mask


def load_images_from_folder(parent_folder: str, folder: str, load_cap: int = 0, skip_from_first: int = 0) -> tuple:
    """Loads images from a ComfyUI folder. Returns (output_images, output_masks) lists."""
    _, abs_path = resolve_comfy_path(parent_folder, folder)

    if not os.path.isdir(abs_path):
        return [], []

    valid_extensions = [".png", ".jpg", ".jpeg", ".webp"]
    image_files = sorted([
        f for f in os.listdir(abs_path)
        if any(f.lower().endswith(ext) for ext in valid_extensions)
    ])

    skip_from_first = max(0, int(skip_from_first))
    load_cap = max(0, int(load_cap))

    if skip_from_first:
        image_files = image_files[skip_from_first:]
    if load_cap > 0:
        image_files = image_files[:load_cap]

    if not image_files:
        return [], []

    output_images = []
    output_masks = []
    for file in image_files:
        image_path = os.path.join(abs_path, file)
        image, mask = load_image(image_path)
        output_images.append(image)
        output_masks.append(mask)

    return output_images, output_masks


def get_model_from_csv(is_config: bool, model_type: str, model_name:str):
    csv_data = _load_csv_as_dict(is_config, model_type)
    data = {}
    for row in csv_data:
        if row["name"] == model_name:
            data = row
    return data
