import asyncio
import os
from pathlib import Path

from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING
from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path


class InoS3UploadFile(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3UploadFile",
            display_name="Ino S3 Upload File",
            category="InoS3Helper",
            description="Uploads a local file to S3. If s3_path_key contains a filename, its stem is used with the local file's extension. Otherwise the local filename is used.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_path_key", default=""),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default=""),
                io.Boolean.Input("delete_local", default=True),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="s3_file_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, s3_path_key, parent_folder, folder, filename, delete_local, s3_config=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_path_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], "")

        _, abs_path = resolve_comfy_path(parent_folder, folder, filename)

        validate_local_path = S3Helper.validate_local_path(Path(abs_path))
        if not validate_local_path["success"]:
            return io.NodeOutput(False, validate_local_path["msg"], "")

        local_ext = Path(filename).suffix

        s3_path = Path(s3_path_key)
        if s3_path.suffix:
            # s3_path_key has a filename — use its stem + local file extension
            s3_full_key = str(s3_path.with_suffix(local_ext))
        else:
            # s3_path_key is a directory — append local filename
            s3_full_key = f"{s3_path_key.rstrip('/')}/{filename}"

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], "")
        async with s3_instance["instance"] as s3_instance:

            s3_result = await s3_instance.upload_file(s3_key=s3_full_key, local_file_path=abs_path)
            if s3_result["success"] and delete_local:
                await asyncio.to_thread(os.remove, abs_path)

            return io.NodeOutput(s3_result["success"], s3_result["msg"], s3_full_key)
