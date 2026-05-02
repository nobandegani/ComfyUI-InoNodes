import asyncio
import shutil
from pathlib import Path

from inopyutils import InoFileHelper

from comfy_api.latest import io

from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path


class InoIncrementBatchName(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoIncrementBatchName",
            display_name="Ino Increment Batch Name",
            category="InoFileHelper",
            description="Increments a batch name string (e.g. Batch_00001 -> Batch_00002).",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.String.Input("name", default="Batch_00001"),
                io.String.Input("dummy_string", optional=True),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, seed, name, dummy_string=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        result = InoFileHelper.increment_batch_name(name=name)
        return io.NodeOutput(result[0])


class InoZip(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoZip",
            display_name="Ino Zip",
            category="InoFileHelper",
            description="Zips a source folder into a zip file at the specified destination.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.Combo.Input("source_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("source_folder", default=""),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default="archive.zip"),
                io.String.Input("dummy_string", optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, seed, source_parent_folder, source_folder, parent_folder, folder, filename, dummy_string=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "")

        _, source_abs = resolve_comfy_path(source_parent_folder, source_folder)
        rel_path, abs_path = resolve_comfy_path(parent_folder, folder, filename)

        Path(abs_path).parent.mkdir(parents=True, exist_ok=True)

        res = await InoFileHelper.zip(
            to_zip=source_abs,
            path_to_save=str(Path(abs_path).parent),
            zip_file_name=Path(abs_path).name
        )
        return io.NodeOutput(res["success"], res["msg"], rel_path, abs_path)


class InoUnzip(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoUnzip",
            display_name="Ino Unzip",
            category="InoFileHelper",
            description="Extracts a zip file to the specified destination folder.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.Combo.Input("source_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("source_folder", default=""),
                io.String.Input("source_filename", default="archive.zip"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("dummy_string", optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, seed, source_parent_folder, source_folder, source_filename, parent_folder, folder, dummy_string=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "")

        _, zip_abs = resolve_comfy_path(source_parent_folder, source_folder, source_filename)
        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)

        res = await InoFileHelper.unzip(zip_path=zip_abs, output_path=abs_path)
        return io.NodeOutput(res["success"], res["msg"], rel_path, abs_path)


class InoRemoveFile(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoRemoveFile",
            display_name="Ino Remove File",
            category="InoFileHelper",
            description="Removes a file from the filesystem.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default=""),
                io.String.Input("dummy_string", optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, seed, parent_folder, folder, filename, dummy_string=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "")

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder, filename)
        res = await InoFileHelper.remove_file(file_path=abs_path)
        return io.NodeOutput(res["success"], res["msg"], rel_path, abs_path)


class InoRemoveFolder(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoRemoveFolder",
            display_name="Ino Remove Folder",
            category="InoFileHelper",
            description="Removes a folder and all its contents recursively.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("dummy_string", optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, seed, parent_folder, folder, dummy_string=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "")

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)
        res = await InoFileHelper.remove_folder(folder_path=Path(abs_path))
        return io.NodeOutput(res["success"], res["msg"], rel_path, abs_path)


class InoCopyFiles(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCopyFiles",
            display_name="Ino Copy Files",
            category="InoFileHelper",
            description="Copies files from one folder to another with optional renaming.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("from_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("from_folder", default=""),
                io.Combo.Input("to_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("to_folder", default=""),
                io.Boolean.Input("iterate_subfolders", default=True),
                io.Boolean.Input("rename_files", default=True),
                io.String.Input("prefix_name", default="file"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="logs"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, from_parent_folder, from_folder, to_parent_folder, to_folder, iterate_subfolders, rename_files, prefix_name) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "", "")

        _, from_abs = resolve_comfy_path(from_parent_folder, from_folder)
        rel_path, abs_path = resolve_comfy_path(to_parent_folder, to_folder)

        res = await InoFileHelper.copy_files(
            to_path=Path(abs_path), from_path=Path(from_abs),
            iterate_subfolders=iterate_subfolders, rename_files=rename_files, prefix_name=prefix_name,
        )
        return io.NodeOutput(res["success"], res["msg"], rel_path, abs_path, res["logs"])


class InoCopyFile(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCopyFile",
            display_name="Ino Copy File",
            category="InoFileHelper",
            description="Copies a single file from one location to another. Preserves modification time and permissions. Leave to_filename empty to keep the source filename.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("from_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("from_folder", default=""),
                io.String.Input("from_filename", default=""),
                io.Combo.Input("to_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("to_folder", default=""),
                io.String.Input("to_filename", default="", optional=True, tooltip="Leave empty to keep the source filename."),
                io.Boolean.Input("overwrite", default=False, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, from_parent_folder, from_folder, from_filename,
                      to_parent_folder, to_folder, to_filename="", overwrite=False) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "")

        if not from_filename:
            return io.NodeOutput(False, "from_filename is required", "", "")

        # Default the destination filename to the source filename if not provided.
        target_filename = to_filename or from_filename

        _, from_abs = resolve_comfy_path(from_parent_folder, from_folder, from_filename)
        rel_path, to_abs = resolve_comfy_path(to_parent_folder, to_folder, target_filename)

        from_path = Path(from_abs)
        to_path = Path(to_abs)

        if not from_path.is_file():
            return io.NodeOutput(False, f"Source file not found: {from_abs}", rel_path, to_abs)

        if to_path.exists() and not overwrite:
            return io.NodeOutput(False, f"Destination already exists (overwrite=False): {to_abs}", rel_path, to_abs)

        try:
            await asyncio.to_thread(to_path.parent.mkdir, parents=True, exist_ok=True)
            # shutil.copy2 preserves mtime + permissions, like the move helper does.
            await asyncio.to_thread(shutil.copy2, str(from_path), str(to_path))
        except Exception as e:
            return io.NodeOutput(False, f"Copy failed: {e}", rel_path, to_abs)

        return io.NodeOutput(True, "copied", rel_path, to_abs)


class InoCountFiles(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCountFiles",
            display_name="Ino Count Files",
            category="InoFileHelper",
            description="Counts files in a folder, optionally recursively.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.Boolean.Input("recursive", default=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.Int.Output(display_name="count"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, parent_folder, folder, recursive) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "", 0)

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)
        res = await InoFileHelper.count_files(path=Path(abs_path), recursive=recursive)
        return io.NodeOutput(res["success"], res["msg"], rel_path, abs_path, res["count"])


class InoValidateMediaFiles(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoValidateMediaFiles",
            display_name="Ino Validate Media Files",
            category="InoFileHelper",
            description="Validates and categorizes media files, separating valid from invalid images and videos.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.Boolean.Input("include_images", default=True),
                io.Boolean.Input("include_videos", default=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="skipped_images_path"),
                io.String.Output(display_name="skipped_images_unsupported_path"),
                io.String.Output(display_name="skipped_videos_path"),
                io.String.Output(display_name="skipped_videos_unsupported_path"),
                io.String.Output(display_name="unsupported_files_path"),
                io.String.Output(display_name="logs"),
                io.String.Output(display_name="output_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, parent_folder, folder, include_images, include_videos) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "", "", "", "", "", "", "", "")

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)

        res = await InoFileHelper.validate_files(
            input_path=Path(abs_path), include_image=include_images, include_video=include_videos,
        )
        return io.NodeOutput(
            True, res.get("msg"), rel_path, abs_path,
            res.get("skipped_images_path"), res.get("skipped_images_unsupported_path"),
            res.get("skipped_videos_path"), res.get("skipped_videos_unsupported_path"),
            res.get("unsupported_files_path"), res.get("logs"), abs_path,
        )


class InoRemoveDuplicateFiles(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoRemoveDuplicateFiles",
            display_name="Ino Remove Duplicate Files",
            category="InoFileHelper",
            description="Removes duplicate files from a folder using hash comparison.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.Boolean.Input("recursive", default=True),
                io.Int.Input("chunk_size", default=32, min=8, max=1024, step=8, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="removed_list"),
                io.Int.Output(display_name="removed_count"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, parent_folder, folder, recursive, chunk_size=32) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "", "", 0)

        rel_path, abs_path = resolve_comfy_path(parent_folder, folder)
        res = await InoFileHelper.remove_duplicate_files(input_path=Path(abs_path), recursive=recursive, chunk_size=chunk_size)
        return io.NodeOutput(res["success"], res["msg"], rel_path, abs_path, res["removed"], res["removed_count"])


class InoGetLastFile(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetLastFile",
            display_name="Ino Get Last File",
            category="InoFileHelper",
            description="Returns the most recently modified file in a folder.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="filename"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, parent_folder, folder) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "")

        _, abs_path = resolve_comfy_path(parent_folder, folder)
        res = await asyncio.to_thread(InoFileHelper.get_last_file, path=Path(abs_path))
        if not res["success"]:
            return io.NodeOutput(False, res["msg"], "", "")
        return io.NodeOutput(True, res["msg"], res.get("file_name", ""), res.get("file_path", ""))


class InoMovePath(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoMovePath",
            display_name="Ino Move Path",
            category="InoFileHelper",
            description="Moves a file or folder from one location to another with optional overwrite.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("from_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("from_folder", default=""),
                io.String.Input("from_filename", default="", optional=True),
                io.Combo.Input("to_parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("to_folder", default=""),
                io.String.Input("to_filename", default="", optional=True),
                io.Boolean.Input("overwrite", default=False, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, from_parent_folder, from_folder, from_filename="",
                      to_parent_folder="output", to_folder="", to_filename="", overwrite=False) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "", "")

        _, from_abs = resolve_comfy_path(from_parent_folder, from_folder, from_filename)
        rel_path, to_abs = resolve_comfy_path(to_parent_folder, to_folder, to_filename)

        res = await InoFileHelper.move_path(from_path=from_abs, to_path=to_abs, overwrite=overwrite)
        return io.NodeOutput(res["success"], res["msg"], rel_path, to_abs)


class InoGetFileHash(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetFileHash",
            display_name="Ino Get File Hash",
            category="InoFileHelper",
            description="Computes the SHA-256 hash of a file.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default=""),
                io.Int.Input("chunk_size", default=8, min=1, max=1024, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="hash"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, parent_folder, folder, filename, chunk_size=8) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "")

        _, abs_path = resolve_comfy_path(parent_folder, folder, filename)
        res = await InoFileHelper.get_file_hash_sha_256(file_path=Path(abs_path), chunk_size=chunk_size)
        if not res["success"]:
            return io.NodeOutput(False, res["msg"], "")
        return io.NodeOutput(True, res["msg"], res.get("hash", ""))


class InoFileToBase64(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoFileToBase64",
            display_name="Ino File To Base64",
            category="InoFileHelper",
            description="Converts a file to a base64 data URI string with auto MIME type detection.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default=""),
                io.String.Input("mime_type", default="", optional=True, tooltip="Leave empty for auto detection"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="data_uri"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, parent_folder, folder, filename, mime_type="") -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(False, "Node is disabled", "")

        _, abs_path = resolve_comfy_path(parent_folder, folder, filename)
        mime = mime_type if mime_type else None
        res = await InoFileHelper.file_to_base64_data_uri(file_path=abs_path, mime_type=mime)
        if not res["success"]:
            return io.NodeOutput(False, res["msg"], "")
        return io.NodeOutput(True, res["msg"], res.get("data_uri", ""))


LOCAL_NODE_CLASS = {
    "InoIncrementBatchName": InoIncrementBatchName,
    "InoZip": InoZip,
    "InoUnzip": InoUnzip,
    "InoRemoveFile": InoRemoveFile,
    "InoRemoveFolder": InoRemoveFolder,
    "InoCopyFiles": InoCopyFiles,
    "InoCopyFile": InoCopyFile,
    "InoCountFiles": InoCountFiles,
    "InoValidateMediaFiles": InoValidateMediaFiles,
    "InoRemoveDuplicateFiles": InoRemoveDuplicateFiles,
    "InoGetLastFile": InoGetLastFile,
    "InoMovePath": InoMovePath,
    "InoGetFileHash": InoGetFileHash,
    "InoFileToBase64": InoFileToBase64,
}
LOCAL_NODE_NAME = {
    "InoIncrementBatchName": "Ino Increment Batch Name",
    "InoZip": "Ino Zip",
    "InoUnzip": "Ino Unzip",
    "InoRemoveFile": "Ino Remove File",
    "InoRemoveFolder": "Ino Remove Folder",
    "InoCopyFiles": "Ino Copy Files",
    "InoCopyFile": "Ino Copy File",
    "InoCountFiles": "Ino Count Files",
    "InoValidateMediaFiles": "Ino Validate Media Files",
    "InoRemoveDuplicateFiles": "Ino Remove Duplicate Files",
    "InoGetLastFile": "Ino Get Last File",
    "InoMovePath": "Ino Move Path",
    "InoGetFileHash": "Ino Get File Hash",
    "InoFileToBase64": "Ino File To Base64",
}
