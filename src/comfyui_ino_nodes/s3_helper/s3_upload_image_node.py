import os
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
from inopyutils import ino_is_err, InoUtilHelper

import folder_paths
from comfy.cli_args import args
from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


class InoS3UploadImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3UploadImage",
            display_name="Ino S3 Upload Image",
            category="InoS3Helper",
            description="Saves a single image as PNG to temp then uploads it to S3. Only supports one image (batch size 1).",
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

        temp_path = folder_paths.get_temp_directory()
        save_dir = os.path.join(temp_path, "s3_upload_image")
        os.makedirs(save_dir, exist_ok=True)

        i = 255. * image[0].cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        metadata = None
        if not args.disable_metadata:
            metadata = PngInfo()

        local_name = InoUtilHelper.get_date_time_utc_base64()
        local_file = f"{local_name}.png"
        full_path = os.path.join(save_dir, local_file)
        img.save(full_path, pnginfo=metadata, compress_level=compress_level)
        img.close()

        s3_name = local_name if unique_file_name else Path(filename).stem
        s3_file = f"{s3_name}.png"

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(image, False, s3_instance["msg"], "", "")
        s3_instance = s3_instance["instance"]

        s3_full_key = f"{s3_path_key.rstrip('/')}/{s3_file}"
        s3_result = await s3_instance.upload_file(s3_key=s3_full_key, local_file_path=full_path)
        if not s3_result["success"]:
            return io.NodeOutput(image, False, s3_result["msg"], "", "")

        return io.NodeOutput(image, True, "Success", s3_file, s3_full_key)
