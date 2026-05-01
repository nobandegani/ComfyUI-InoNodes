import asyncio
import base64
import io as std_io
import torch
import os
import math
from pathlib import Path

from torchvision.transforms import InterpolationMode
import torchvision.transforms.functional as TorchFunctional
from datetime import datetime, timezone
from PIL import Image
import numpy as np

import nodes
import folder_paths
from comfy_api.latest import io

from inopyutils import InoJsonHelper, ino_is_err

from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path, load_image, load_images_from_folder

MAX_RESOLUTION = nodes.MAX_RESOLUTION


def _batch_images(images, padding):
    from collections import Counter
    from comfy.utils import common_upscale

    processed = []
    if padding:
        max_h = max(img.shape[1] for img in images)
        max_w = max(img.shape[2] for img in images)
        for img in images:
            h, w = img.shape[1], img.shape[2]
            if h != max_h or w != max_w:
                padded = torch.zeros(1, max_h, max_w, img.shape[3])
                y_offset = (max_h - h) // 2
                x_offset = (max_w - w) // 2
                padded[:, y_offset:y_offset + h, x_offset:x_offset + w, :] = img
                processed.append(padded)
            else:
                processed.append(img)
    else:
        sizes = Counter((img.shape[1], img.shape[2]) for img in images)
        target_h, target_w = sizes.most_common(1)[0][0]
        for img in images:
            if img.shape[1] != target_h or img.shape[2] != target_w:
                img = img.movedim(-1, 1)
                img = common_upscale(img, target_w, target_h, "lanczos", "center")
                img = img.movedim(1, -1)
            processed.append(img)

    return torch.cat(processed, dim=0)


class InoSaveImages(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoSaveImages",
            display_name="Ino Save Images",
            category="InoImageHelper",
            description="Saves images to a specified folder with a filename prefix.",
            is_output_node=True,
            inputs=[
                io.Image.Input("images", tooltip="The images to save."),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename_prefix", default="ComfyUI", tooltip="The prefix for the file to save."),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Int.Output(display_name="number_of_images"),
                io.String.Output(display_name="datetime_iso"),
            ],
        )

    @classmethod
    async def execute(cls, images, parent_folder, folder, filename_prefix) -> io.NodeOutput:
        time_now = datetime.now(timezone.utc).isoformat()

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)
        _, parent_dir = resolve_comfy_path(parent_folder)

        prefix = f"{folder}/{filename_prefix}" if folder else filename_prefix

        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            prefix, parent_dir,
            images[0].shape[1], images[0].shape[0]
        )

        from PIL import Image as PILImage
        from comfy.cli_args import args
        from PIL.PngImagePlugin import PngInfo

        images_cpu = [img.cpu().numpy() for img in images]
        include_metadata = not args.disable_metadata

        def _save_all():
            saved = []
            local_counter = counter
            for batch_number, arr in enumerate(images_cpu):
                pil_img = PILImage.fromarray(np.clip(255. * arr, 0, 255).astype(np.uint8))
                metadata = PngInfo() if include_metadata else None
                filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
                file = f"{filename_with_batch_num}_{local_counter:05}_.png"
                pil_img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=4)
                saved.append({"filename": file, "subfolder": subfolder, "type": parent_folder})
                local_counter += 1
            return saved

        results = await asyncio.to_thread(_save_all)

        if len(results) == 0:
            return io.NodeOutput(False, "No images saved", rel_path, abs_path, 0, time_now)

        names = [r["filename"] for r in results]
        return io.NodeOutput(True, str(names), rel_path, abs_path, len(results), time_now)


class InoImageResizeByLongerSideV1(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoImageResizeByLongerSideV1",
            display_name="Ino Image Resize By Longer Side V1",
            category="InoImageHelper",
            description="Resizes an image so the longer side matches the specified size, preserving aspect ratio.",
            inputs=[
                io.Image.Input("image"),
                io.Int.Input("size", default=512, min=0, max=99999, step=1),
                io.Combo.Input("interpolation_mode", options=["bicubic", "bilinear", "nearest", "nearest exact"]),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
        )

    @classmethod
    def execute(cls, image, size, interpolation_mode) -> io.NodeOutput:
        interp = interpolation_mode.upper().replace(" ", "_")
        interp = getattr(InterpolationMode, interp)

        _, h, w, _ = image.shape

        if h >= w:
            new_h = size
            new_w = round(w * new_h / h)
        else:
            new_w = size
            new_h = round(h * new_w / w)

        image = image.permute(0, 3, 1, 2)
        image = TorchFunctional.resize(
            image,
            (new_h, new_w),
            interpolation=interp,
            antialias=True,
        )
        image = image.permute(0, 2, 3, 1)

        return io.NodeOutput(image)


class InoImageResizeByLongerSideAndCropV2(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoImageResizeByLongerSideAndCropV2",
            display_name="Ino Image Resize By Longer Side And Crop V2",
            category="InoImageHelper",
            description="Resizes an image to fit target dimensions with optional cropping and position control.",
            inputs=[
                io.Image.Input("image"),
                io.Int.Input("target_width", default=512, min=1, max=MAX_RESOLUTION, step=1),
                io.Int.Input("target_height", default=512, min=1, max=MAX_RESOLUTION, step=1),
                io.Combo.Input("padding_color", options=["white", "black"]),
                io.Combo.Input("interpolation", options=["area", "bicubic", "nearest-exact", "bilinear", "lanczos"]),
                io.Boolean.Input("crop", default=True),
                io.Combo.Input("position", options=["top-left", "top-center", "center", "bottom-center", "bottom-right"]),
                io.Int.Input("x", default=0, min=0, max=MAX_RESOLUTION, step=1),
                io.Int.Input("y", default=0, min=0, max=MAX_RESOLUTION, step=1),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
        )

    @classmethod
    def execute(cls, image, target_width, target_height, padding_color, interpolation, crop, position, x, y) -> io.NodeOutput:
        from comfy_extras.nodes_images import ImageCrop, ResizeAndPadImage
        source_width = int(image.shape[2])
        source_height = int(image.shape[1])

        source_is_width_larger = source_width > source_height
        target_is_width_larger = target_width > target_height

        if source_is_width_larger and target_is_width_larger:
            resize_width = target_width
            resize_height = round((target_width / source_width) * source_height)
        else:
            resize_height = target_height
            resize_width = round((target_height / source_height) * source_width)

        resizer = ResizeAndPadImage()
        resized_image = resizer.resize_and_pad(image, resize_width, resize_height, padding_color, interpolation)

        if not crop:
            return io.NodeOutput(resized_image[0])

        cropper = ImageCrop()
        canvas = resized_image[0]
        canvas_h = int(canvas.shape[1])
        canvas_w = int(canvas.shape[2])

        def clamp(val, lo, hi):
            return max(lo, min(val, hi))

        crop_x = int(x)
        crop_y = int(y)

        center_x = max(0, (canvas_w - int(target_width)) // 2)
        right_x = max(0, canvas_w - int(target_width))
        center_y = max(0, (canvas_h - int(target_height)) // 2)
        bottom_y = max(0, canvas_h - int(target_height))

        if position == "top-left":
            crop_x, crop_y = 0, 0
        elif position == "top-center":
            crop_x, crop_y = center_x, 0
        elif position == "center":
            crop_x, crop_y = center_x, center_y
        elif position == "bottom-center":
            crop_x, crop_y = center_x, bottom_y
        elif position == "bottom-right":
            crop_x, crop_y = right_x, bottom_y

        crop_x = clamp(crop_x, 0, max(0, canvas_w - 1))
        crop_y = clamp(crop_y, 0, max(0, canvas_h - 1))

        cropped_image = cropper.crop(canvas, int(target_width), int(target_height), int(crop_x), int(crop_y))

        return io.NodeOutput(cropped_image[0])


class InoResizeCropImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoResizeCropImage",
            display_name="Ino Resize Crop Image",
            category="InoImageHelper",
            description="Resizes an image to cover the target width/height, then crops to the exact size at the selected position.",
            inputs=[
                io.Image.Input("image"),
                io.Int.Input("width", default=512, min=1, max=MAX_RESOLUTION, step=1),
                io.Int.Input("height", default=512, min=1, max=MAX_RESOLUTION, step=1),
                io.Combo.Input("crop_position", options=[
                    "top-left", "top-center", "top-right",
                    "center-left", "center", "center-right",
                    "bottom-left", "bottom-center", "bottom-right",
                ], default="center"),
                io.Combo.Input("interpolation", options=["lanczos", "bicubic", "bilinear", "area", "nearest-exact"], default="lanczos"),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
        )

    @classmethod
    def execute(cls, image, width, height, crop_position, interpolation) -> io.NodeOutput:
        from comfy.utils import common_upscale

        target_w = int(width)
        target_h = int(height)
        src_h = int(image.shape[1])
        src_w = int(image.shape[2])

        scale = max(target_w / src_w, target_h / src_h)
        resize_w = max(target_w, int(round(src_w * scale)))
        resize_h = max(target_h, int(round(src_h * scale)))

        img = image.movedim(-1, 1)
        img = common_upscale(img, resize_w, resize_h, interpolation, "disabled")
        img = img.movedim(1, -1)

        canvas_h = int(img.shape[1])
        canvas_w = int(img.shape[2])

        if "left" in crop_position:
            x = 0
        elif "right" in crop_position:
            x = max(0, canvas_w - target_w)
        else:
            x = max(0, (canvas_w - target_w) // 2)

        if "top" in crop_position:
            y = 0
        elif "bottom" in crop_position:
            y = max(0, canvas_h - target_h)
        else:
            y = max(0, (canvas_h - target_h) // 2)

        cropped = img[:, y:y + target_h, x:x + target_w, :]
        return io.NodeOutput(cropped)


class InoLoadImagesFromFolder(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoLoadImagesFromFolder",
            display_name="Ino Load Images From Folder",
            category="InoImageHelper",
            description="Loads images from a folder with optional skip and cap. Returns images, masks, and count.",
            inputs=[
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder"),
                io.Int.Input("load_cap", default=0, min=0, max=10000),
                io.Int.Input("skip_from_first", default=0, min=0, max=10000),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Image.Output(display_name="images", is_output_list=True),
                io.Mask.Output(display_name="masks", is_output_list=True),
                io.Int.Output(display_name="number of images"),
            ],
        )

    @classmethod
    def execute(cls, parent_folder, folder, load_cap, skip_from_first) -> io.NodeOutput:
        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)
        output_images, output_masks = load_images_from_folder(parent_folder, folder, load_cap, skip_from_first)
        if not output_images:
            from nodes import EmptyImage
            empty_image = EmptyImage().generate(512, 512)[0]
            empty_mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu").unsqueeze(0)
            return io.NodeOutput(False, "No images found", rel_path, abs_path, [empty_image], [empty_mask], 0)
        return io.NodeOutput(True, f"Loaded {len(output_images)} images", rel_path, abs_path, output_images, output_masks, len(output_images))


class InoLoadImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoLoadImage",
            display_name="Ino Load Image",
            category="InoImageHelper",
            description="Loads a single image from input/output/temp by parent_folder + folder + filename. Returns (success, message, rel_path, abs_path, image, mask).",
            inputs=[
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default=""),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Image.Output(display_name="image"),
                io.Mask.Output(display_name="mask"),
            ],
        )

    @classmethod
    async def execute(cls, parent_folder, folder, filename) -> io.NodeOutput:
        rel_path, abs_path = resolve_comfy_path(parent_folder, folder, filename)

        def _empty():
            from nodes import EmptyImage
            empty_image = EmptyImage().generate(512, 512)[0]
            empty_mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu").unsqueeze(0)
            return empty_image, empty_mask

        if not filename:
            empty_image, empty_mask = _empty()
            return io.NodeOutput(False, "filename is required", rel_path, abs_path, empty_image, empty_mask)

        if not Path(abs_path).is_file():
            empty_image, empty_mask = _empty()
            return io.NodeOutput(False, f"File not found: {abs_path}", rel_path, abs_path, empty_image, empty_mask)

        try:
            # load_image is synchronous (PIL + torch) — offload to a thread.
            image, mask = await asyncio.to_thread(load_image, abs_path)
        except Exception as e:
            empty_image, empty_mask = _empty()
            return io.NodeOutput(False, f"Failed to load image: {e}", rel_path, abs_path, empty_image, empty_mask)

        return io.NodeOutput(True, "loaded", rel_path, abs_path, image, mask)


class InoImageListToBatch(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoImageListToBatch",
            display_name="Ino Image List To Batch",
            category="InoImageHelper",
            description="Combines a list of images into a single batched tensor, with resize or pad options.",
            is_input_list=True,
            inputs=[
                io.Image.Input("images"),
                io.Boolean.Input("padding", default=False, label_off="Resize", label_on="Pad"),
            ],
            outputs=[
                io.Image.Output(display_name="images"),
                io.Int.Output(display_name="number of images"),
            ],
        )

    @classmethod
    def execute(cls, images, padding) -> io.NodeOutput:
        padding = padding[0] if isinstance(padding, list) else padding
        if len(images) == 0:
            return io.NodeOutput(torch.empty(0), 0)
        batched = _batch_images(images, padding)
        return io.NodeOutput(batched, len(images))


class InoCropImageByBox(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCropImageByBox",
            display_name="Ino Crop Image By Box",
            category="InoImageHelper",
            description="Crops an image to a square region around a point with adjustable shift offsets.",
            inputs=[
                io.Image.Input("image"),
                io.Int.Input("x", default=0, min=0, max=10000),
                io.Int.Input("y", default=0, min=0, max=10000),
                io.Float.Input("shift_x", default=0.5, min=0, max=1, step=0.1),
                io.Float.Input("shift_y", default=0.5, min=0, max=1, step=0.1),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
        )

    @classmethod
    def execute(cls, image, x, y, shift_x, shift_y) -> io.NodeOutput:
        height = int(image.shape[1])
        width = int(image.shape[2])

        crop_size = int(min(width, height))

        crop_x = int(round(float(x) - (crop_size * float(shift_x))))
        crop_y = int(round(float(y) - (crop_size * float(shift_y))))

        crop_x = max(0, min(crop_x, width - crop_size))
        crop_y = max(0, min(crop_y, height - crop_size))

        to_x = crop_x + crop_size
        to_y = crop_y + crop_size

        img = image[:, crop_y:to_y, crop_x:to_x, :]
        return io.NodeOutput(img)


class InoOnImageListCompleted(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoOnImageListCompleted",
            display_name="Ino On Image List Completed",
            category="InoImageHelper",
            description="Tracks image processing progress with a persistent counter stored in the folder.",
            is_output_node=True,
            inputs=[
                io.Image.Input("input_image"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder"),
                io.Int.Input("count", default=0, min=0, max=10000),
            ],
            outputs=[
                io.Image.Output(display_name="output_image"),
                io.Int.Output(display_name="current"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    async def execute(cls, input_image, parent_folder, folder, count) -> io.NodeOutput:
        _, abs_path = resolve_comfy_path(parent_folder, folder)

        counter_path = Path(abs_path) / "counter.json"

        counter_json = {"counter": 1}
        if counter_path.exists():
            counter_file = await InoJsonHelper.read_json_from_file_async(
                str(counter_path.resolve()),
            )
            if ino_is_err(counter_file):
                return io.NodeOutput(input_image, 0)
            counter_json = counter_file["data"]
            counter_json["counter"] = int(counter_json["counter"]) + 1

        counter_file = await InoJsonHelper.save_json_as_json_async(
            counter_json,
            str(counter_path.resolve()),
        )
        if ino_is_err(counter_file):
            return io.NodeOutput(input_image, 0)

        return io.NodeOutput(input_image, counter_json["counter"])


class InoImageToBase64(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoImageToBase64",
            display_name="Ino Image To Base64",
            category="InoImageHelper",
            description="Converts an image to a base64-encoded data URL string.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Image.Input("image"),
                io.Combo.Input("format", options=["png", "jpeg", "webp"], default="png"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="base64_string"),
            ],
        )

    @classmethod
    def execute(cls, enabled, image, format="png") -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "")

        try:
            img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)

            mime_map = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}
            mime = mime_map[format]

            buffer = std_io.BytesIO()
            pil_image.save(buffer, format=format.upper())
            b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return io.NodeOutput(True, f"data:{mime};base64,{b64}")
        except Exception as e:
            return io.NodeOutput(False, str(e))


class InoImagesFromFolderToReferenceLatent(io.ComfyNode):
    upscale_methods = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoImagesFromFolderToReferenceLatent",
            display_name="Ino Images From Folder To Reference Latent",
            category="InoImageHelper",
            description="Loads images from a folder, scales them, and encodes as reference latents for conditioning.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder"),
                io.Int.Input("load_cap", default=0, min=0, max=10000),
                io.Int.Input("skip_from_first", default=0, min=0, max=10000),
                io.Combo.Input("upscale_method", options=cls.upscale_methods, default="lanczos"),
                io.Float.Input("megapixels", default=1.0, min=0.01, max=16.0, step=0.01),
                io.Int.Input("resolution_steps", default=1, min=1, max=256),
                io.Vae.Input("vae"),
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative", optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Image.Output(display_name="images", is_output_list=True),
                io.Latent.Output(display_name="latents", is_output_list=True),
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Int.Output(display_name="number of images"),
            ],
        )

    @classmethod
    def execute(cls, enabled, parent_folder, folder, load_cap, skip_from_first, upscale_method, megapixels, resolution_steps, vae, positive, negative=None) -> io.NodeOutput:
        from comfy_extras.nodes_edit_model import ReferenceLatent
        from nodes import VAEEncode

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)

        vae_encoder = VAEEncode()

        from nodes import EmptyImage
        empty_image = EmptyImage().generate(512, 512)[0]
        empty_latent = vae_encoder.encode(vae, empty_image)[0]

        if not enabled:
            return io.NodeOutput(False, "Node is disabled", rel_path, abs_path, [empty_image], [empty_latent], positive, negative, 0)

        from comfy_extras.nodes_post_processing import ImageScaleToTotalPixels

        images, _ = load_images_from_folder(parent_folder, folder, load_cap, skip_from_first)

        if not images:
            return io.NodeOutput(False, "No images found", rel_path, abs_path, [empty_image], [empty_latent], positive, negative, 0)

        scaled_images = []
        for img in images:
            scaled = ImageScaleToTotalPixels.execute(img, upscale_method, megapixels, resolution_steps).args[0]
            scaled_images.append(scaled)

        latents = []
        pos_cond = positive
        neg_cond = negative

        for img in scaled_images:
            latent = vae_encoder.encode(vae, img)[0]
            latents.append(latent)
            pos_cond = ReferenceLatent.execute(pos_cond, latent).args[0]
            if neg_cond is not None:
                neg_cond = ReferenceLatent.execute(neg_cond, latent).args[0]

        return io.NodeOutput(True, f"Loaded {len(images)} images", rel_path, abs_path, images, latents, pos_cond, neg_cond, len(images))


class InoImagesToReferenceLatent(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoImagesToReferenceLatent",
            display_name="Ino Images To Reference Latent",
            category="InoImageHelper",
            description="Encodes a batch of images as reference latents and applies them to conditioning.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Image.Input("images"),
                io.Vae.Input("vae"),
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative", optional=True),
            ],
            outputs=[
                io.Latent.Output(display_name="latents", is_output_list=True),
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
            ],
        )

    @classmethod
    def execute(cls, enabled, images, vae, positive, negative=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput([], positive, negative)

        from comfy_extras.nodes_edit_model import ReferenceLatent
        from nodes import VAEEncode

        vae_encoder = VAEEncode()
        latents = []
        pos_cond = positive
        neg_cond = negative

        for i in range(images.shape[0]):
            img = images[i].unsqueeze(0)
            latent = vae_encoder.encode(vae, img)[0]
            latents.append(latent)
            pos_cond = ReferenceLatent.execute(pos_cond, latent).args[0]
            if neg_cond is not None:
                neg_cond = ReferenceLatent.execute(neg_cond, latent).args[0]

        return io.NodeOutput(latents, pos_cond, neg_cond)


class InoIsImagePortrait(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoIsImagePortrait",
            display_name="Ino Is Image Portrait",
            category="InoImageHelper",
            description="Returns True if the image height is greater than its width.",
            inputs=[
                io.Image.Input("image"),
            ],
            outputs=[
                io.Boolean.Output(display_name="is_portrait"),
            ],
        )

    @classmethod
    def execute(cls, image) -> io.NodeOutput:
        _, h, w, _ = image.shape
        return io.NodeOutput(h > w)


class InoIsImageLandscape(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoIsImageLandscape",
            display_name="Ino Is Image Landscape",
            category="InoImageHelper",
            description="Returns True if the image width is greater than its height.",
            inputs=[
                io.Image.Input("image"),
            ],
            outputs=[
                io.Boolean.Output(display_name="is_landscape"),
            ],
        )

    @classmethod
    def execute(cls, image) -> io.NodeOutput:
        _, h, w, _ = image.shape
        return io.NodeOutput(w > h)


class InoIsImageSquare(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoIsImageSquare",
            display_name="Ino Is Image Square",
            category="InoImageHelper",
            description="Returns True if the image width equals its height.",
            inputs=[
                io.Image.Input("image"),
            ],
            outputs=[
                io.Boolean.Output(display_name="is_square"),
            ],
        )

    @classmethod
    def execute(cls, image) -> io.NodeOutput:
        _, h, w, _ = image.shape
        return io.NodeOutput(h == w)


import math

ASPECT_RATIO_OPTIONS = [
    "1:1 Square",
    "9:16 Vertical Video",
    "16:9 Widescreen",
    "4:5 Social Media",
    "5:4 Classic Monitor",
    "3:4 Tablet",
    "4:3 Standard TV",
    "2:3 Film Photo",
    "3:2 DSLR Photo",
    "5:7 Print",
    "7:5 Print Wide",
    "1:2 Tall Banner",
    "2:1 Panoramic",
    "6:13 iPhone Portrait",
    "13:6 iPhone Landscape",
    "9:20 Android Portrait",
    "20:9 Android Landscape",
]

ASPECT_RATIO_MAP = {
    "1:1 Square": (1, 1),
    "9:16 Vertical Video": (9, 16),
    "16:9 Widescreen": (16, 9),
    "4:5 Social Media": (4, 5),
    "5:4 Classic Monitor": (5, 4),
    "3:4 Tablet": (3, 4),
    "4:3 Standard TV": (4, 3),
    "2:3 Film Photo": (2, 3),
    "3:2 DSLR Photo": (3, 2),
    "5:7 Print": (5, 7),
    "7:5 Print Wide": (7, 5),
    "1:2 Tall Banner": (1, 2),
    "2:1 Panoramic": (2, 1),
    "6:13 iPhone Portrait": (6, 13),
    "13:6 iPhone Landscape": (13, 6),
    "9:20 Android Portrait": (9, 20),
    "20:9 Android Landscape": (20, 9),
}


class InoMegapixelResolution(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoMegapixelResolution",
            display_name="Ino Megapixel Resolution",
            category="InoImageHelper",
            description="Calculate width and height from megapixels and aspect ratio.",
            inputs=[
                io.Float.Input("megapixels", default=1.0, min=0.01, max=100.0, step=0.01),
                io.Combo.Input("aspect_ratio", options=ASPECT_RATIO_OPTIONS, default="1:1 Square"),
                io.String.Input("custom_aspect_ratio", default=""),
                io.Int.Input("divisible_by", default=16, min=1, max=512),
            ],
            outputs=[
                io.Int.Output(display_name="width"),
                io.Int.Output(display_name="height"),
                io.Int.Output(display_name="aspect_ratio_x"),
                io.Int.Output(display_name="aspect_ratio_y"),
                io.String.Output(display_name="aspect_ratio"),
            ],
        )

    @classmethod
    def execute(cls, megapixels, aspect_ratio, custom_aspect_ratio, divisible_by) -> io.NodeOutput:
        # Parse aspect ratio
        custom = custom_aspect_ratio.strip()
        if custom and ":" in custom:
            parts = custom.split(":")
            try:
                ar_x = int(parts[0].strip())
                ar_y = int(parts[1].strip())
                if ar_x <= 0 or ar_y <= 0:
                    raise ValueError("Aspect ratio values must be positive")
            except (ValueError, IndexError):
                ar_x, ar_y = ASPECT_RATIO_MAP.get(aspect_ratio, (1, 1))
        else:
            ar_x, ar_y = ASPECT_RATIO_MAP.get(aspect_ratio, (1, 1))

        total_pixels = megapixels * 1_000_000

        # width / height = ar_x / ar_y
        # width * height = total_pixels
        # width = sqrt(total_pixels * ar_x / ar_y)
        raw_width = math.sqrt(total_pixels * ar_x / ar_y)
        raw_height = math.sqrt(total_pixels * ar_y / ar_x)

        # Round to nearest divisible_by
        width = max(divisible_by, round(raw_width / divisible_by) * divisible_by)
        height = max(divisible_by, round(raw_height / divisible_by) * divisible_by)

        ar_string = f"{ar_x}:{ar_y}"

        return io.NodeOutput(width, height, ar_x, ar_y, ar_string)


LOCAL_NODE_CLASS = {
    "InoSaveImages": InoSaveImages,
    "InoImageResizeByLongerSideV1": InoImageResizeByLongerSideV1,
    "InoImageResizeByLongerSideAndCropV2": InoImageResizeByLongerSideAndCropV2,
    "InoResizeCropImage": InoResizeCropImage,
    "InoLoadImage": InoLoadImage,
    "InoLoadImagesFromFolder": InoLoadImagesFromFolder,
    "InoOnImageListCompleted": InoOnImageListCompleted,
    "InoCropImageByBox": InoCropImageByBox,
    "InoImageToBase64": InoImageToBase64,
    "InoImagesToReferenceLatent": InoImagesToReferenceLatent,
    "InoImagesFromFolderToReferenceLatent": InoImagesFromFolderToReferenceLatent,
    "InoImageListToBatch": InoImageListToBatch,
    "InoIsImagePortrait": InoIsImagePortrait,
    "InoIsImageLandscape": InoIsImageLandscape,
    "InoIsImageSquare": InoIsImageSquare,
    "InoMegapixelResolution": InoMegapixelResolution,
}
LOCAL_NODE_NAME = {
    "InoSaveImages": "Ino Save Images",
    "InoImageResizeByLongerSideV1": "Ino Image Resize By Longer Side V1",
    "InoImageResizeByLongerSideAndCropV2": "Ino Image Resize By Longer Side And Crop V2",
    "InoResizeCropImage": "Ino Resize Crop Image",
    "InoLoadImage": "Ino Load Image",
    "InoLoadImagesFromFolder": "Ino Load Images From Folder",
    "InoOnImageListCompleted": "Ino On Image List Completed",
    "InoCropImageByBox": "Ino Crop Image By Box",
    "InoImageToBase64": "Ino Image To Base64",
    "InoImagesToReferenceLatent": "Ino Images To Reference Latent",
    "InoImagesFromFolderToReferenceLatent": "Ino Images From Folder To Reference Latent",
    "InoImageListToBatch": "Ino Image List To Batch",
    "InoIsImagePortrait": "Ino Is Image Portrait",
    "InoIsImageLandscape": "Ino Is Image Landscape",
    "InoIsImageSquare": "Ino Is Image Square",
    "InoMegapixelResolution": "Ino Megapixel Resolution",
}
