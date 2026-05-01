from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


# AWS SigV4 caps presigned URL lifetimes at 7 days.
_MAX_EXPIRES_IN = 7 * 24 * 3600  # 604800 seconds


class InoS3GetDownloadURL(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3GetDownloadURL",
            display_name="Ino S3 Get Download URL",
            category="InoS3Helper",
            description="Generates a presigned download URL for an S3 object.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default="input/example.png"),
                io.Int.Input("expires_in", default=3600, min=1, max=_MAX_EXPIRES_IN, step=1, tooltip="Link lifetime in seconds (max 7 days = 604800)."),
                io.Boolean.Input("as_attachment", default=False),
                io.String.Input("filename", default="", tooltip="Optional download filename. Leave empty to default to the object's basename."),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="download_url"),
                io.String.Output(display_name="filename"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, s3_key, expires_in=3600, as_attachment=False, filename="", s3_config=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", "", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], "", "")

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], "", "")
        async with s3_instance["instance"] as s3_instance:

            # Helper expects None (not "") to fall back to the object's basename.
            suggested_filename = filename or None

            s3_result = await s3_instance.get_download_link(
                s3_key=s3_key,
                expires_in=expires_in,
                as_attachment=as_attachment,
                filename=suggested_filename,
            )
            return io.NodeOutput(
                s3_result.get("success", False),
                s3_result.get("msg", ""),
                s3_result.get("url", ""),
                s3_result.get("filename", ""),
            )
