import os
from pathlib import Path

from inopyutils import ino_is_err, InoUtilHelper

import folder_paths
from comfy_api.latest import io, Input, Types

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


class InoS3UploadVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3UploadVideo",
            display_name="Ino S3 Upload Video",
            category="InoS3Helper",
            description="Saves video to temp then uploads it to S3.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Video.Input("video"),
                io.String.Input("s3_path_key", default=""),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Combo.Input("video_format", options=["mp4", "auto"], optional=True),
                io.Combo.Input("video_codec", options=["h264", "auto"], optional=True),
                io.Boolean.Input("unique_file_name", default=True, optional=True, label_off="Use filename", label_on="Unique name"),
                io.String.Input("filename", default="", optional=True),
            ],
            outputs=[
                io.Video.Output(display_name="video"),
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="file_name"),
                io.String.Output(display_name="s3_video_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, video: Input.Video, s3_path_key, filename, s3_config=None, unique_file_name=True, video_format="mp4", video_codec="h264") -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(video, False, "", "", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_path_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(video, False, validate_s3_key["msg"], "", "")

        temp_path = folder_paths.get_temp_directory()
        save_dir = os.path.join(temp_path, "s3_upload_video")
        os.makedirs(save_dir, exist_ok=True)

        ext = Types.VideoContainer.get_extension(video_format)
        local_name = InoUtilHelper.get_date_time_utc_base64()
        local_file = f"{local_name}.{ext}"
        full_path = os.path.join(save_dir, local_file)

        video.save_to(full_path, format=Types.VideoContainer(video_format), codec=Types.VideoCodec(video_codec))

        s3_name = local_name if unique_file_name else Path(filename).stem
        s3_file = f"{s3_name}.{ext}"

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(video, False, s3_instance["msg"], "", "")
        s3_instance = s3_instance["instance"]

        s3_full_key = f"{s3_path_key.rstrip('/')}/{s3_file}"
        s3_result = await s3_instance.upload_file(s3_key=s3_full_key, local_file_path=full_path)

        return io.NodeOutput(video, s3_result["success"], s3_result["msg"], s3_file, s3_full_key)
