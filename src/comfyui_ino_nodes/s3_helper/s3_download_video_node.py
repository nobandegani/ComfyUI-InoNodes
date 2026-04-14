import os
from pathlib import Path

from inopyutils import ino_is_err, InoUtilHelper

import folder_paths
from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


class InoS3DownloadVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3DownloadVideo",
            display_name="Ino S3 Download Video",
            category="InoS3Helper",
            description="Downloads a video file from S3 and returns it as a VIDEO type.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default="input/example.mp4"),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.Video.Output(display_name="video"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, s3_key, s3_config=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", None)

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], None)

        temp_path = folder_paths.get_temp_directory()
        save_dir = os.path.join(temp_path, "s3_download_video")
        os.makedirs(save_dir, exist_ok=True)

        random_str = InoUtilHelper.get_date_time_utc_base64()
        file_name = f'{random_str}{Path(s3_key).suffix}'
        full_path = os.path.join(save_dir, file_name)

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], None)
        s3_instance = s3_instance["instance"]

        downloaded = await s3_instance.download_file(s3_key=s3_key, local_file_path=full_path)
        if not downloaded["success"]:
            return io.NodeOutput(False, downloaded["msg"], None)

        from comfy_api.latest import VideoFromFile
        video = VideoFromFile(full_path)

        return io.NodeOutput(True, "Success", video)
