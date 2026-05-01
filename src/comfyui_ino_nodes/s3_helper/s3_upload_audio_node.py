import asyncio
import os
from pathlib import Path

from inopyutils import ino_is_err, InoUtilHelper

import folder_paths
from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING


class InoS3UploadAudio(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3UploadAudio",
            display_name="Ino S3 Upload Audio",
            category="InoS3Helper",
            description="Saves audio as MP3 then uploads it to S3.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Audio.Input("audio"),
                io.String.Input("s3_path_key", default=""),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Boolean.Input("unique_file_name", default=True, optional=True, label_off="Use filename", label_on="Unique name"),
                io.String.Input("filename", default="", optional=True),
                io.Boolean.Input("delete_local", default=True, optional=True, tooltip="Delete the locally saved MP3 after a successful S3 upload."),
            ],
            outputs=[
                io.Audio.Output(display_name="audio"),
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="file_name"),
                io.String.Output(display_name="s3_audio_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, audio, s3_path_key, filename, s3_config=None, unique_file_name=True, delete_local=True) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(audio, False, "", "", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_path_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(audio, False, validate_s3_key["msg"], "", "")

        local_name = InoUtilHelper.get_date_time_utc_base64()

        # SaveAudioMP3 writes the MP3 to ComfyUI's output directory and
        # returns a UI payload with the final filename. We reuse it instead
        # of re-implementing MP3 encoding, then upload the resulting file.
        from comfy_extras.nodes_audio import SaveAudioMP3

        try:
            save_audio = SaveAudioMP3.execute(
                audio=audio, filename_prefix=local_name, format="mp3", quality="128k"
            )
        except Exception as e:
            return io.NodeOutput(audio, False, f"Failed to save audio: {e}", "", "")

        try:
            saved_filename = save_audio.ui.as_dict()["audio"][0]["filename"]
        except (AttributeError, KeyError, IndexError, TypeError) as e:
            return io.NodeOutput(audio, False, f"Audio saved but failed to read result filename: {e}", "", "")

        output_path = folder_paths.get_output_directory()
        full_path = str((Path(output_path) / saved_filename).resolve())

        s3_name = local_name if unique_file_name else (Path(filename).stem or local_name)
        s3_file = f"{s3_name}.mp3"

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(audio, False, s3_instance["msg"], "", "")
        s3_instance = s3_instance["instance"]

        s3_full_key = f"{s3_path_key.rstrip('/')}/{s3_file}"
        s3_result = await s3_instance.upload_file(s3_key=s3_full_key, local_file_path=full_path)
        if not s3_result["success"]:
            return io.NodeOutput(audio, False, s3_result["msg"], "", "")

        if delete_local:
            try:
                await asyncio.to_thread(os.remove, full_path)
            except OSError:
                # Non-fatal — upload succeeded.
                pass

        return io.NodeOutput(audio, True, s3_result.get("msg", "Success"), s3_file, s3_full_key)
