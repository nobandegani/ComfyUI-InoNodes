import os
from pathlib import Path

from inopyutils import InoS3Helper, InoJsonHelper, ino_ok, ino_err, ino_is_err

from comfy_api.latest import io

S3_EMPTY_CONFIG = {
    "access_key_id": "",
    "access_key_secret": "",
    "bucket_name": "",
    "endpoint_url": "",
    "region_name": "",
}
S3_EMPTY_CONFIG_STRING = InoJsonHelper.dict_to_string(S3_EMPTY_CONFIG)["data"]

class S3Helper:
    @staticmethod
    def get_instance(s3_config:str) -> dict:
        validate = S3Helper.validate_s3_config(s3_config)
        if ino_is_err(validate):
            return validate

        s3_config = validate["config"]

        try:
            s3_instance = InoS3Helper()
            s3_instance.init(
                aws_access_key_id=s3_config["access_key_id"],
                aws_secret_access_key=s3_config["access_key_secret"],
                endpoint_url=s3_config["endpoint_url"],
                region_name=s3_config["region_name"],
                bucket_name=s3_config["bucket_name"],
            )
            return ino_ok("success", instance=s3_instance)
        except Exception as e:
            return ino_err(f"Failed to create S3 instance: {e}")

    @staticmethod
    def validate_s3_config(s3_config:str) -> dict:
        if not s3_config:
            return {
                "success": False,
                "msg": "S3 configuration is required and cannot be empty",
                "config": ""
            }

        s3_config_dict = InoJsonHelper.string_to_dict(s3_config)
        if not s3_config_dict["success"]:
            return {
                "success": False,
                "msg": "S3 configuration must be a valid json string",
                "config": ""
            }
        s3_config_dict = s3_config_dict["data"]

        # Overlay env vars on top of the JSON config. Only override when the
        # env var is set to a non-empty value, so callers can leave fields
        # empty in the JSON and have env vars populate them — without an
        # accidental empty-string env var clobbering a real JSON value.
        env_map = {
            "access_key_id": "S3_ACCESS_KEY",
            "access_key_secret": "S3_ACCESS_SECRET",
            "endpoint_url": "S3_ENDPOINT_URL",
            "region_name": "S3_REGION_NAME",
            "bucket_name": "S3_BUCKET_NAME",
        }
        for field, env_name in env_map.items():
            env_val = os.getenv(env_name)
            if env_val:
                s3_config_dict[field] = env_val
            else:
                s3_config_dict.setdefault(field, "")

        if not s3_config_dict.get("access_key_id"):
            return {
                "success": False,
                "msg": "S3 configuration missing access_key_id",
                "config": ""
            }

        if not s3_config_dict.get("access_key_secret"):
            return {
                "success": False,
                "msg": "S3 configuration missing access_key_secret",
                "config": ""
            }

        return {
            "success": True,
            "msg": "S3 configuration is valid",
            "config": s3_config_dict
        }

    @staticmethod
    def validate_s3_key(s3_key) -> dict:
        if not s3_key or not s3_key.strip():
            return {"success": False, "msg": "S3 key is required and cannot be empty"}
        return {"success": True, "msg": "S3 key is valid"}

    @staticmethod
    def validate_local_path(local_path) -> dict:
        if not local_path:
            return {"success": False, "msg": "Local path is required and cannot be empty"}
        if not Path(local_path).is_file() and not Path(local_path).is_dir():
            return {"success": False, "msg": "Local path does not exist"}
        return {"success": True, "msg": "Local path is valid"}

    @staticmethod
    def get_save_path(s3_key: str, save_path: str):
        save_path_obj = Path(save_path)
        s3_key_obj = Path(s3_key)

        if save_path.endswith('/') or save_path.endswith('\\'):
            local_file_path = save_path_obj / s3_key_obj.name
        elif save_path_obj.suffix:
            filename_without_ext = save_path_obj.stem
            s3_extension = s3_key_obj.suffix
            local_file_path = save_path_obj.parent / (filename_without_ext + s3_extension)
        else:
            s3_extension = s3_key_obj.suffix
            local_file_path = Path(save_path + s3_extension)

        return local_file_path


class InoS3Config(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3Config",
            display_name="Ino S3 Config",
            category="InoS3Helper",
            description="Creates an S3 configuration string from credentials.",
            inputs=[
                io.String.Input("access_key_id", default=""),
                io.String.Input("access_key_secret", default=""),
                io.String.Input("endpoint_url", default=""),
                io.String.Input("region_name", default=""),
                io.String.Input("bucket_name", default=""),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="config"),
            ],
        )

    @classmethod
    async def execute(cls, access_key_id, access_key_secret, endpoint_url, region_name, bucket_name) -> io.NodeOutput:
        s3_config = {
            "access_key_id": access_key_id,
            "access_key_secret": access_key_secret,
            "endpoint_url": endpoint_url,
            "region_name": region_name,
            "bucket_name": bucket_name,
        }
        dict_to_string = InoJsonHelper.dict_to_string(s3_config)
        if not dict_to_string["success"]:
            return io.NodeOutput(False, dict_to_string["msg"])
        return io.NodeOutput(True, dict_to_string["data"])
