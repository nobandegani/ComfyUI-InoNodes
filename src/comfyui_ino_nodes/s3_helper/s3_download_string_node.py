from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


class InoS3DownloadString(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3DownloadString",
            display_name="Ino S3 Download String",
            category="InoS3Helper",
            description="Downloads a text object from S3 directly into memory and returns its content as a string.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default="input/example.txt"),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.String.Input("encoding", default="utf-8", optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, s3_key, s3_config=None, encoding="utf-8") -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], "")

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], "")
        async with s3_instance["instance"] as s3_instance:

            result = await s3_instance.get_text(s3_key=s3_key, encoding=encoding)
            if not result["success"]:
                return io.NodeOutput(False, result["msg"], "")

            return io.NodeOutput(True, result.get("msg", "Success"), result.get("text", ""))
