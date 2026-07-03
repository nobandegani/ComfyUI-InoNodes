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
                io.Combo.Input("quality", options=["V0", "128k", "320k"], default="128k", optional=True, tooltip="MP3 encoding quality."),
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
    async def execute(cls, enabled, audio, s3_path_key, filename, s3_config=None, unique_file_name=True, delete_local=True, quality="128k") -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(audio, False, "", "", "")

        validate_s3_key = S3Helper.validate_s3_key(s3_path_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(audio, False, validate_s3_key["msg"], "", "")

        local_name = InoUtilHelper.get_date_time_utc_base64()

        # Encode the MP3 with AudioSaveHelper instead of SaveAudioMP3.execute:
        # output nodes read cls.hidden, which is only populated on their own
        # execution clone, so invoking one from another node crashes (issue #3).
        # Passing our own cls keeps the workflow metadata embedded in the file;
        # it is skipped when execute() is called outside the executor, where
        # cls.hidden is None.
        from comfy_api.latest import ui

        metadata_cls = cls if getattr(cls, "hidden", None) is not None else None
        try:
            save_audio = ui.AudioSaveHelper.get_save_audio_ui(
                audio, filename_prefix=local_name, cls=metadata_cls, format="mp3", quality=quality,
            )
        except Exception as e:
            return io.NodeOutput(audio, False, f"Failed to save audio: {e}", "", "")

        try:
            saved = save_audio.results[0]
            saved_filename = str(Path(saved.subfolder) / saved.filename) if saved.subfolder else saved.filename
        except (AttributeError, IndexError, TypeError) as e:
            return io.NodeOutput(audio, False, f"Audio saved but failed to read result filename: {e}", "", "")

        output_path = folder_paths.get_output_directory()
        full_path = str((Path(output_path) / saved_filename).resolve())

        s3_name = local_name if unique_file_name else (Path(filename).stem or local_name)
        s3_file = f"{s3_name}.mp3"

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(audio, False, s3_instance["msg"], "", "")
        async with s3_instance["instance"] as s3_instance:

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
