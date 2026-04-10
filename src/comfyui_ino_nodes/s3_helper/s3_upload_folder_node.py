import shutil
from pathlib import Path

from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING
from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path, FailureInvalidatesCacheMixin


class InoS3UploadFolder(FailureInvalidatesCacheMixin, io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3UploadFolder",
            display_name="Ino S3 Upload Folder",
            category="InoS3Helper",
            description="Uploads an entire local folder to S3 with concurrent uploads and optional verification.",
            is_output_node=True,
            inputs=[
                io.AnyType.Input("execute"),
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default=""),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.Boolean.Input("delete_local", default=True),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Int.Input("max_concurrent", default=8, min=1, max=16, optional=True),
                io.Boolean.Input("verify_with_s3", default=False, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Int.Output(display_name="total_files"),
                io.Int.Output(display_name="uploaded_successfully"),
                io.Int.Output(display_name="failed_uploads"),
                io.String.Output(display_name="errors"),
            ],
        )

    @classmethod
    async def execute(cls, execute, enabled, s3_key, parent_folder, folder, delete_local, s3_config=None, max_concurrent=5, verify_with_s3=False) -> io.NodeOutput:
        if not enabled:
            cls._bump_failure()
            return io.NodeOutput(False, "", "", "", 0, 0, 0, "")
        if not execute:
            cls._bump_failure()
            return io.NodeOutput(False, "", "", "", 0, 0, 0, "")

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            cls._bump_failure()
            return io.NodeOutput(False, validate_s3_key["msg"], "", "", 0, 0, 0, "")

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)

        validate_local_path = S3Helper.validate_local_path(Path(abs_path))
        if not validate_local_path["success"]:
            cls._bump_failure()
            return io.NodeOutput(False, validate_local_path["msg"], rel_path, abs_path, 0, 0, 0, "")

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            cls._bump_failure()
            return io.NodeOutput(False, s3_instance["msg"], rel_path, abs_path, 0, 0, 0, "")
        s3_instance = s3_instance["instance"]

        s3_result = await s3_instance.upload_folder(s3_folder_key=s3_key, local_folder_path=abs_path, max_concurrent=max_concurrent, verify=verify_with_s3)
        if s3_result["success"] and delete_local:
            shutil.rmtree(Path(abs_path))

        return io.NodeOutput(cls._track(s3_result["success"]), s3_result["msg"], rel_path, abs_path, s3_result["total_files"], s3_result["uploaded_successfully"], s3_result["failed_uploads"], str(s3_result["errors"]))
