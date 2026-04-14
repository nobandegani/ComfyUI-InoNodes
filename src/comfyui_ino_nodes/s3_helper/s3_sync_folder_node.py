from pathlib import Path

from inopyutils import ino_is_err

from comfy_api.latest import io

from .s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING
from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path


class InoS3SyncFolder(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3SyncFolder",
            display_name="Ino S3 Sync Folder",
            category="InoS3Helper",
            description="Syncs a local folder with S3 bidirectionally (upload or download).",
            is_output_node=True,
            inputs=[
                io.AnyType.Input("execute"),
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("s3_key", default=""),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default="sync/"),
                io.Boolean.Input("sync_local", default=True, label_off="Upload (local->S3)", label_on="Download (S3->local)"),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
                io.Int.Input("concurrency", default=5, min=1, max=10, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Int.Output(display_name="downloaded"),
                io.Int.Output(display_name="uploaded"),
                io.Int.Output(display_name="skipped_unchanged"),
                io.Int.Output(display_name="failed"),
            ],
        )

    @classmethod
    async def execute(cls, execute, enabled, s3_key, parent_folder, folder, sync_local, s3_config=None, concurrency=5) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "not enabled", "", "", 0, 0, 0, 0)
        if not execute:
            return io.NodeOutput(False, "execute empty", "", "", 0, 0, 0, 0)

        validate_s3_key = S3Helper.validate_s3_key(s3_key)
        if not validate_s3_key["success"]:
            return io.NodeOutput(False, validate_s3_key["msg"], "", "", 0, 0, 0, 0)

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)

        local_folder_path = Path(abs_path)
        if not local_folder_path.is_dir():
            local_folder_path.mkdir(parents=True, exist_ok=True)

        s3_instance = S3Helper.get_instance(s3_config)
        if ino_is_err(s3_instance):
            return io.NodeOutput(False, s3_instance["msg"], "", "", 0, 0, 0, 0)
        s3_instance = s3_instance["instance"]

        s3_result = await s3_instance.sync_folder(s3_key=s3_key, local_folder_path=abs_path, sync_local=sync_local, concurrency=concurrency)

        return io.NodeOutput(
            s3_result["success"], s3_result["msg"], rel_path, abs_path,
            s3_result.get("downloaded", 0), s3_result.get("uploaded", 0),
            s3_result.get("skipped_unchanged", 0), s3_result.get("failed", 0),
        )
