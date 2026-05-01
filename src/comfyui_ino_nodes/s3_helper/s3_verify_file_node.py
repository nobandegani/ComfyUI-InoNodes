from pathlib import Path

from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING
from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path


class InoS3VerifyFile(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3VerifyFile",
            display_name="Ino S3 Verify File",
            category="InoS3Helper",
            description="Verifies a local file exists in S3 and optionally checks integrity via hash.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default=""),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default=""),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Boolean.Input("use_md5", default=False, optional=True),
                io.Boolean.Input("use_sha256", default=False, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Boolean.Output(display_name="exists_remote"),
                io.Boolean.Output(display_name="sizes_match"),
                io.String.Output(display_name="verify_method"),
                io.Int.Output(display_name="local_size"),
                io.Int.Output(display_name="remote_size"),
                io.String.Output(display_name="etag"),
                io.Boolean.Output(display_name="md5_match"),
                io.Boolean.Output(display_name="sha256_match"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, s3_key, parent_folder, folder, filename, s3_config=None, use_md5=False, use_sha256=False) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", "", "", False, False, "", 0, 0, "", False, False)

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], "", "", False, False, "", 0, 0, "", False, False)

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder, filename)

        validate_local_path = S3Helper.validate_local_path(Path(abs_path))
        if not validate_local_path["success"]:
            return io.NodeOutput(False, validate_local_path["msg"], rel_path, abs_path, False, False, "", 0, 0, "", False, False)

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], rel_path, abs_path, False, False, "", 0, 0, "", False, False)
        async with s3_instance["instance"] as s3_instance:

            s3_result = await s3_instance.verify_file(local_file_path=abs_path, s3_key=s3_key, use_md5=use_md5, use_sha256=use_sha256)

            return io.NodeOutput(
                s3_result["success"],
                s3_result["msg"],
                rel_path,
                abs_path,
                bool(s3_result.get("exists_remote", False)),
                bool(s3_result.get("sizes_match", False)),
                str(s3_result.get("verify_method") or ""),
                int(s3_result.get("local_size") or 0),
                int(s3_result.get("remote_size") or 0),
                str(s3_result.get("etag") or ""),
                bool(s3_result.get("md5_match") or False),
                bool(s3_result.get("sha256_match") or False),
            )
