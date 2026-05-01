from pathlib import Path

from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING
from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path


class InoS3DownloadFolder(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3DownloadFolder",
            display_name="Ino S3 Download Folder",
            category="InoS3Helper",
            description="Downloads an entire folder from S3 with concurrent downloads.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default="input/example.png"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default="input/"),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Int.Input("max_concurrent", default=8, min=1, max=16, optional=True),
                io.Boolean.Input("verify", default=False, optional=True, tooltip="If True, verify folder sync after download (skipped if download had failures)."),
                io.Boolean.Input("overwrite", default=False, optional=True, tooltip="If False (default), per file skip when the local file already matches S3."),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Int.Output(display_name="total_files"),
                io.Int.Output(display_name="downloaded_successfully"),
                io.Int.Output(display_name="skipped_files"),
                io.Int.Output(display_name="failed_downloads"),
                io.String.Output(display_name="errors"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, s3_key, parent_folder, folder, s3_config=None, max_concurrent=8, verify=False, overwrite=False) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", "", "", 0, 0, 0, 0, "")

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], "", "", 0, 0, 0, 0, "")

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)

        if Path(abs_path).is_file():
            return io.NodeOutput(False, "Save path is a file", rel_path, abs_path, 0, 0, 0, 0, "")

        if not Path(abs_path).is_dir():
            Path(abs_path).mkdir(parents=True, exist_ok=True)

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], rel_path, abs_path, 0, 0, 0, 0, "")
        s3_instance = s3_instance["instance"]

        s3_result = await s3_instance.download_folder(
            s3_folder_key=s3_key,
            local_folder_path=abs_path,
            max_concurrent=max_concurrent,
            verify=verify,
            overwrite=overwrite,
        )
        return io.NodeOutput(
            s3_result["success"],
            s3_result["msg"],
            rel_path,
            abs_path,
            int(s3_result.get("total_files", 0)),
            int(s3_result.get("downloaded_successfully", 0)),
            int(s3_result.get("skipped_files", 0)),
            int(s3_result.get("failed_downloads", 0)),
            str(s3_result.get("errors", "")),
        )
