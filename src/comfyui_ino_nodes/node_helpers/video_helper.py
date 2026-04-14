import asyncio
import os
import random
import string

import folder_paths
from comfy_api.latest import io, ui, Input, Types


class InoPreviewVideo(io.ComfyNode):
    _prefix_append = "_temp_" + ''.join(random.choice(string.ascii_lowercase) for _ in range(5))

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoPreviewVideo",
            display_name="Ino Preview Video",
            category="InoVideoHelper",
            description="Saves a video to the temp directory for in-node preview.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Video.Input("video"),
                io.Combo.Input("format", options=["mp4", "webm", "auto"], default="mp4", optional=True),
                io.Combo.Input("codec", options=["h264", "auto"], default="h264", optional=True),
            ],
            outputs=[],
        )

    @classmethod
    async def execute(cls, enabled, video: Input.Video, format="mp4", codec="h264") -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(ui=ui.PreviewVideo([]).as_dict())

        width, height = video.get_dimensions()
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            "ComfyUI" + cls._prefix_append, folder_paths.get_temp_directory(), width, height
        )

        file = f"{filename}_{counter:05}_.{Types.VideoContainer.get_extension(format)}"
        await asyncio.to_thread(
            video.save_to,
            os.path.join(full_output_folder, file),
            format=Types.VideoContainer(format),
            codec=Types.VideoCodec(codec),
        )

        return io.NodeOutput(ui=ui.PreviewVideo([ui.SavedResult(file, subfolder, io.FolderType.temp)]).as_dict())


LOCAL_NODE_CLASS = {"InoPreviewVideo": InoPreviewVideo}
LOCAL_NODE_NAME = {"InoPreviewVideo": "Ino Preview Video"}
