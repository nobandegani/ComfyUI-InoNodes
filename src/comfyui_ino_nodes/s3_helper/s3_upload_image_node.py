import asyncio
import io as std_io
import os
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
from inopyutils import ino_is_err, InoUtilHelper

from comfy.cli_args import args
from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


def _encode_png_bytes(image_tensor, compress_level: int, include_metadata: bool) -> bytes:
    """Encode a single-image torch tensor (B=1, H, W, C) as PNG bytes in-memory."""
    arr = 255.0 * image_tensor[0].cpu().numpy()
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    metadata = PngInfo() if include_metadata else None
    buf = std_io.BytesIO()
    try:
        img.save(buf, format="PNG", pnginfo=metadata, compress_level=compress_level)
    finally:
        img.close()
    return buf.getvalue()


class InoS3UploadImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3UploadImage",
            display_name="Ino S3 Upload Image",
            category="InoS3Helper",
            description="Encodes a single image as PNG in memory and uploads it directly to S3. Only supports one image (batch size 1).",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Image.Input("image"),
                io.String.Input("s3_path_key", default=""),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Int.Input("compress_level", default=4, min=1, max=9, optional=True),
                io.Boolean.Input("unique_file_name", default=True, optional=True, label_off="Use filename", label_on="Unique name"),
                io.String.Input("filename", default="", optional=True),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="file_name"),
                io.String.Output(display_name="s3_image_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, image, s3_path_key, filename, s3_config=None, compress_level=4, unique_file_name=True) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(image, False, "", "", "")

        if image.shape[0] > 1:
            return io.NodeOutput(image, False, "Only one image supported, received batch of " + str(image.shape[0]), "", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_path_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(image, False, validate_s3_key["msg"], "", "")

        local_name = InoUtilHelper.get_date_time_utc_base64()
        s3_name = local_name if unique_file_name else (Path(filename).stem or local_name)
        s3_file = f"{s3_name}.png"

        # PIL encoding is CPU-bound — offload off the event loop.
        try:
            png_bytes = await asyncio.to_thread(
                _encode_png_bytes,
                image,
                compress_level,
                not args.disable_metadata,
            )
        except Exception as e:
            return io.NodeOutput(image, False, f"Failed to encode image: {e}", "", "")

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(image, False, s3_instance["msg"], "", "")
        s3_instance = s3_instance["instance"]

        s3_full_key = f"{s3_path_key.rstrip('/')}/{s3_file}"
        s3_result = await s3_instance.put_bytes(
            data=png_bytes,
            s3_key=s3_full_key,
            content_type="image/png",
        )
        if not s3_result["success"]:
            return io.NodeOutput(image, False, s3_result["msg"], "", "")

        return io.NodeOutput(image, True, s3_result.get("msg", "Success"), s3_file, s3_full_key)
