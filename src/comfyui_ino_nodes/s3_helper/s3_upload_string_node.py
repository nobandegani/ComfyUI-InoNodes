from pathlib import Path

from inopyutils import ino_is_err, InoUtilHelper

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


_CONTENT_TYPE_MAP = {
    "txt": "text/plain; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "ini": "text/plain; charset=utf-8",
}


class InoS3UploadString(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3UploadString",
            display_name="Ino S3 Upload String",
            category="InoS3Helper",
            description="Uploads a string directly to S3 as a text object (no temp file).",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("string"),
                io.Combo.Input("save_as", options=["txt", "json", "ini"]),
                io.String.Input("s3_path_key", default=""),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Boolean.Input("unique_file_name", default=True, optional=True, label_off="Use filename", label_on="Unique name"),
                io.String.Input("filename", default="", optional=True),
            ],
            outputs=[
                io.String.Output(display_name="string"),
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="file_name"),
                io.String.Output(display_name="s3_string_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, string, save_as, s3_path_key, filename, s3_config=None, unique_file_name=True) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(string, False, "", "", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_path_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(string, False, validate_s3_key["msg"], "", "")

        local_name = InoUtilHelper.get_date_time_utc_base64()
        s3_name = local_name if unique_file_name else (Path(filename).stem or local_name)
        s3_file = f"{s3_name}.{save_as}"

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(string, False, s3_instance["msg"], "", "")
        async with s3_instance["instance"] as s3_instance:

            s3_full_key = f"{s3_path_key.rstrip('/')}/{s3_file}"
            content_type = _CONTENT_TYPE_MAP.get(save_as, "text/plain; charset=utf-8")
            s3_result = await s3_instance.put_text(text=string, s3_key=s3_full_key, content_type=content_type)
            if not s3_result["success"]:
                return io.NodeOutput(string, False, s3_result["msg"], "", "")

            return io.NodeOutput(string, True, s3_result.get("msg", "Success"), s3_file, s3_full_key)
