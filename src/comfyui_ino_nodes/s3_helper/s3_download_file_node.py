from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING
from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path


class InoS3DownloadFile(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3DownloadFile",
            display_name="Ino S3 Download File",
            category="InoS3Helper",
            description="Downloads a file from S3 to a local folder.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default="input/example.png"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default="s3download/"),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Boolean.Input("overwrite", default=False, optional=True, tooltip="If False (default), skip the download when the local file already matches the remote (sha256/md5/size cascade)."),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, s3_key, parent_folder, folder, s3_config=None, overwrite=False) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", "", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], "", "")

        save_path = S3Helper.get_save_path(s3_key, folder)
        rel_path, abs_path = resolve_comfy_path(parent_folder, str(save_path))

        # download_file already creates the parent dir; no client-side mkdir needed.

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], "", "")
        async with s3_instance["instance"] as s3_instance:

            s3_result = await s3_instance.download_file(s3_key=s3_key, local_file_path=abs_path, overwrite=overwrite)
            return io.NodeOutput(s3_result["success"], s3_result["msg"], rel_path, abs_path)
