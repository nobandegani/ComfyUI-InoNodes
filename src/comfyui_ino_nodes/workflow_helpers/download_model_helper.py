import asyncio
import os
import shutil

from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download
from inopyutils import InoJsonHelper, InoHttpHelper, ino_is_err, InoCivitHelper

import folder_paths

from comfy_api.latest import io

from ..s3_helper.s3_helper import S3Helper, S3_EMPTY_CONFIG_STRING
from ..node_helper import ino_print_log, MODEL_TYPES
from ..node_helper import get_list_from_csv, get_model_from_csv


class InoCreateDownloadModelConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCreateModelFileConfig",
            display_name="Ino Create Model File Config",
            category="InoModelHelper",
            description="Creates a model download configuration from individual fields.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("host", options=["s3", "hf", "civitai"]),
                io.Combo.Input("model_type", options=list(MODEL_TYPES)),
                io.String.Input("model_subfolder", default="flux1dev"),
                io.String.Input("repo_id", default="", tooltip="depends on the host."),
                io.String.Input("filename", default="", tooltip="depends on the host."),
                io.String.Input("subfolder", default="", tooltip="depends on the host."),
                io.String.Input("repo_type", default="", tooltip="depends on the host."),
                io.String.Input("revision", default="", tooltip="depends on the host."),
            ],
            outputs=[
                io.String.Output(display_name="ModelConfig"),
            ],
        )

    @classmethod
    def execute(cls, enabled, host, model_type, model_subfolder, repo_id, filename, subfolder, repo_type, revision) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoCreateDownloadModelConfig", "Attempt to run but disabled")
            return io.NodeOutput("")

        config = {
            "host": host,
            "model_type": model_type,
            "model_subfolder": model_subfolder,
            "repo_id": repo_id,
            "filename": filename,
            "subfolder": subfolder,
            "repo_type": repo_type,
            "revision": revision,
        }
        config_str = InoJsonHelper.dict_to_string(config)["data"]
        ino_print_log("InoCreateDownloadModelConfig", "config created")
        return io.NodeOutput(config_str)


class InoGetImageModelDownloadConfig(io.ComfyNode):
    MODELS_LIST = get_list_from_csv(False, "image_models_files", True)

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetImageModelDownloadConfig",
            display_name="Ino Get Image Model Download Config",
            category="InoModelHelper",
            description="Retrieves image model download configuration from CSV.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("model", options=cls.MODELS_LIST),
            ],
            outputs=[
                io.String.Output(display_name="ModelConfig"),
            ],
        )

    @classmethod
    def execute(cls, enabled, model) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        model_dict = get_model_from_csv(False, "image_models_files", model)
        data = InoJsonHelper.dict_to_string(model_dict)["data"]
        return io.NodeOutput(data)


class InoGetVideoModelDownloadConfig(io.ComfyNode):
    MODELS_LIST = get_list_from_csv(False, "video_models_files", True)

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetVideoModelDownloadConfig",
            display_name="Ino Get Video Model Download Config",
            category="InoModelHelper",
            description="Retrieves video model download configuration from CSV.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("model", options=cls.MODELS_LIST),
            ],
            outputs=[
                io.String.Output(display_name="ModelConfig"),
            ],
        )

    @classmethod
    def execute(cls, enabled, model) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        model_dict = get_model_from_csv(False, "video_models_files", model)
        data = InoJsonHelper.dict_to_string(model_dict)["data"]
        return io.NodeOutput(data)


class InoGetVaeDownloadConfig(io.ComfyNode):
    MODELS_LIST = get_list_from_csv(False, "vae_files", True)

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetVaeDownloadConfig",
            display_name="Ino Get Vae Download Config",
            category="InoModelHelper",
            description="Retrieves VAE model download configuration from CSV.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("model", options=cls.MODELS_LIST),
            ],
            outputs=[
                io.String.Output(display_name="ModelConfig"),
            ],
        )

    @classmethod
    def execute(cls, enabled, model) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        model_dict = get_model_from_csv(False, "vae_files", model)
        data = InoJsonHelper.dict_to_string(model_dict)["data"]
        return io.NodeOutput(data)


class InoGetClipDownloadConfig(io.ComfyNode):
    MODELS_LIST = get_list_from_csv(False, "clip_files", True)

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetClipDownloadConfig",
            display_name="Ino Get Clip Download Config",
            category="InoModelHelper",
            description="Retrieves CLIP model download configuration from CSV.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("model", options=cls.MODELS_LIST),
            ],
            outputs=[
                io.String.Output(display_name="ModelConfig"),
            ],
        )

    @classmethod
    def execute(cls, enabled, model) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        model_dict = get_model_from_csv(False, "clip_files", model)
        data = InoJsonHelper.dict_to_string(model_dict)["data"]
        return io.NodeOutput(data)


class InoGetControlnetDownloadConfig(io.ComfyNode):
    MODELS_LIST = get_list_from_csv(False, "controlnet_files", True)

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetControlnetDownloadConfig",
            display_name="Ino Get Controlnet Download Config",
            category="InoModelHelper",
            description="Retrieves ControlNet model download configuration from CSV.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("model", options=cls.MODELS_LIST),
            ],
            outputs=[
                io.String.Output(display_name="ModelConfig"),
            ],
        )

    @classmethod
    def execute(cls, enabled, model) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        model_dict = get_model_from_csv(False, "controlnet_files", model)
        data = InoJsonHelper.dict_to_string(model_dict)["data"]
        return io.NodeOutput(data)


class InoGetLoraDownloadConfig(io.ComfyNode):
    MODELS_LIST = get_list_from_csv(False, "lora_files", True)

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetLoraDownloadConfig",
            display_name="Ino Get Lora Download Config",
            category="InoModelHelper",
            description="Retrieves LoRA model download configuration from CSV.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("model", options=cls.MODELS_LIST),
            ],
            outputs=[
                io.String.Output(display_name="ModelConfig"),
            ],
        )

    @classmethod
    def execute(cls, enabled, model) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        model_dict = get_model_from_csv(False, "lora_files", model)
        data = InoJsonHelper.dict_to_string(model_dict)["data"]
        return io.NodeOutput(data)


class InoHttpDownloadModel(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoHttpDownloadModel",
            display_name="Ino Http Download Model",
            category="InoModelHelper",
            description="Downloads a model file from an HTTP URL.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("model_config", default="{}"),
                io.Combo.Input("model_type", options=list(MODEL_TYPES)),
                io.String.Input("model_subfolder", default="flux1dev"),
                io.String.Input("url", default="https://download.pl"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="msg"),
                io.String.Output(display_name="model_type"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="rel_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, model_config, model_type="", model_subfolder="", url="") -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoHttpDownloadModel", "Attempt to run but disabled")
            return io.NodeOutput(False, "", "", "", "")

        try:
            if isinstance(model_config, str):
                input_config = InoJsonHelper.string_to_dict(model_config)
                if input_config["success"]:
                    model_config = input_config["data"]

            if isinstance(model_config, dict):
                model_type = model_config.get("model_type", model_type)
                model_subfolder = model_config.get("model_subfolder", model_subfolder)
                url = model_config.get("filename", url)

            parent_path = Path(folder_paths.get_input_directory()).parent
            model_path_base = parent_path / "models" / model_type
            model_path = model_path_base / model_subfolder / Path(url).name
            rel_path = Path(model_path).relative_to(model_path_base)

            need_download = not model_path.is_file()
            if not need_download:
                ino_print_log("InoHttpDownloadModel", "model already downloaded")
                return io.NodeOutput(True, "model validated", model_type, str(model_path), str(rel_path))

            model_path.parent.mkdir(parents=True, exist_ok=True)

            http_instance = InoHttpHelper()
            http_result = await http_instance.download(
                url=url, dest_path=model_path, resume=True,
                allow_redirects=True, mkdirs=True, connection=6
            )
            if ino_is_err(http_result):
                return io.NodeOutput(False, "failed to download", model_type, str(model_path), str(rel_path))

            ino_print_log("InoHttpDownloadModel", "file downloaded successfully")
            return io.NodeOutput(http_result["success"], http_result["msg"], model_type, str(model_path), str(rel_path))
        except Exception as e:
            ino_print_log("InoHttpDownloadModel", "", e)
            return io.NodeOutput(False, f"Error: {e}", "", "", "")


class InoS3DownloadModel(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoS3DownloadModel",
            display_name="Ino S3 Download Model",
            category="InoModelHelper",
            description="Downloads a model file from S3.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("model_config", default="{}"),
                io.Combo.Input("model_type", options=list(MODEL_TYPES)),
                io.String.Input("model_subfolder", default="flux1dev"),
                io.String.Input("s3_key", default="uploads/lora/aly_v001.safetensors"),
                io.String.Input("s3_config", default=S3_EMPTY_CONFIG_STRING, optional=True, tooltip="you can leave it empty and pass it with env vars"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="msg"),
                io.String.Output(display_name="model_type"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="rel_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, model_config, model_type="", model_subfolder="", s3_key="", s3_config="{}") -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoS3DownloadModel", "Attempt to run but disabled")
            return io.NodeOutput(False, "", "", "", "")

        try:
            if isinstance(model_config, str):
                input_config = InoJsonHelper.string_to_dict(model_config)
                if input_config["success"]:
                    model_config = input_config["data"]

            if isinstance(model_config, dict):
                model_type = model_config.get("model_type", model_type)
                model_subfolder = model_config.get("model_subfolder", model_subfolder)
                s3_config = model_config.get("repo_id", s3_config)
                s3_key = model_config.get("filename", s3_key)

            parent_path = Path(folder_paths.get_input_directory()).parent
            model_path_base = parent_path / "models" / model_type
            model_path = model_path_base / model_subfolder / Path(s3_key).name
            rel_path = Path(model_path).relative_to(model_path_base)

            need_download = not model_path.is_file()
            if not need_download:
                ino_print_log("InoS3DownloadModel", "model already downloaded")
                return io.NodeOutput(True, "model validated", model_type, str(model_path), str(rel_path))

            validate_s3_key = S3Helper.validate_s3_key(s3_key)
            if not validate_s3_key["success"]:
                ino_print_log("InoS3DownloadModel", validate_s3_key["msg"])
                return io.NodeOutput(False, validate_s3_key["msg"], "", "", "")

            model_path.parent.mkdir(parents=True, exist_ok=True)

            s3_instance = S3Helper.get_instance(s3_config)
            if ino_is_err(s3_instance):
                return io.NodeOutput(False, s3_instance["msg"], "", "", "")
            async with s3_instance["instance"] as s3_instance:

                s3_result = await s3_instance.download_file(s3_key=s3_key, local_file_path=model_path)

                ino_print_log("InoS3DownloadModel", "file downloaded successfully")
                return io.NodeOutput(s3_result["success"], s3_result["msg"], model_type, str(model_path), str(rel_path))
        except Exception as e:
            ino_print_log("InoS3DownloadModel", "", e)
            return io.NodeOutput(False, f"Error: {e}", "", "", "")


class InoHuggingFaceDownloadModel(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoHuggingFaceDownloadModel",
            display_name="Ino Hugging Face Download Model",
            category="InoModelHelper",
            description="Downloads a single model file from HuggingFace.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("model_config", default="{}"),
                io.Combo.Input("model_type", options=list(MODEL_TYPES)),
                io.String.Input("model_subfolder", default="flux1dev"),
                io.String.Input("repo_id", default=""),
                io.String.Input("filename", default=""),
                io.String.Input("subfolder", default=""),
                io.String.Input("token", default="", optional=True),
                io.String.Input("repo_type", default="", optional=True),
                io.String.Input("revision", default="", optional=True),
                io.Boolean.Input("ignore_repo_dir", default=False, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="msg"),
                io.String.Output(display_name="model_type"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="rel_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, model_config, model_type="", model_subfolder="", repo_id="", filename="", subfolder="", token="", repo_type="", revision="", ignore_repo_dir=False) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoHuggingFaceDownloadModel", "Attempt to run but disabled")
            return io.NodeOutput(False, "", "", "", "")

        try:
            if isinstance(model_config, str):
                input_config = InoJsonHelper.string_to_dict(model_config)
                if input_config["success"]:
                    model_config = input_config["data"]

            if isinstance(model_config, dict):
                model_type = model_config.get("model_type", model_type)
                model_subfolder = model_config.get("model_subfolder", model_subfolder)
                repo_id = model_config.get("repo_id", repo_id)
                filename = model_config.get("filename", filename)
                subfolder = model_config.get("subfolder", subfolder)
                repo_type = model_config.get("repo_type", repo_type)
                revision = model_config.get("revision", revision)

            parent_path = Path(folder_paths.get_input_directory()).parent
            model_path_base = parent_path / "models" / model_type
            model_path = model_path_base / model_subfolder
            if model_path.is_file():
                model_path = model_path.parent

            args = {}
            if subfolder:
                args["subfolder"] = subfolder
            if token:
                args["token"] = token
            if repo_type:
                args["repo_type"] = repo_type
            if revision:
                args["revision"] = revision
            args["local_dir"] = model_path
        except Exception as e:
            ino_print_log("InoHuggingFaceDownloadModel", "", e)
            return io.NodeOutput(False, f"Error: {e}", "", "", "")

        try:
            result = await asyncio.to_thread(hf_hub_download, repo_id, filename, **args)
            if ignore_repo_dir:
                await asyncio.to_thread(shutil.move, result, model_path)
                result = f"{model_path}/{Path(result).name}"
            rel_path = Path(result).relative_to(model_path_base)
            ino_print_log("InoHuggingFaceDownloadModel", "file downloaded successfully")
            return io.NodeOutput(True, "Successful", model_type, str(result), str(rel_path))
        except Exception as e:
            ino_print_log("InoHuggingFaceDownloadModel", "", e)
            return io.NodeOutput(False, f"Error: {e}", "", "", "")


class InoHuggingFaceDownloadRepo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoHuggingFaceDownloadRepo",
            display_name="Ino Hugging Face Download Repo",
            category="InoModelHelper",
            description="Downloads an entire repository from HuggingFace.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("model_config", default="{}"),
                io.Combo.Input("model_type", options=list(MODEL_TYPES)),
                io.String.Input("model_subfolder", default="flux1dev"),
                io.String.Input("repo_id", default=""),
                io.String.Input("token", default="", optional=True),
                io.String.Input("repo_type", default="", optional=True),
                io.String.Input("revision", default="", optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="msg"),
                io.String.Output(display_name="model_type"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="rel_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, model_config, model_type="", model_subfolder="", repo_id="", token="", repo_type="", revision="") -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoHuggingFaceDownloadRepo", "Attempt to run but disabled")
            return io.NodeOutput(False, "", "", "", "")

        try:
            if isinstance(model_config, str):
                input_config = InoJsonHelper.string_to_dict(model_config)
                if input_config["success"]:
                    model_config = input_config["data"]

            if isinstance(model_config, dict):
                model_type = model_config.get("model_type", model_type)
                model_subfolder = model_config.get("model_subfolder", model_subfolder)
                repo_id = model_config.get("repo_id", repo_id)
                repo_type = model_config.get("repo_type", repo_type)
                revision = model_config.get("revision", revision)

            parent_path = Path(folder_paths.get_input_directory()).parent
            model_path_base = parent_path / "models" / model_type
            model_path = model_path_base / model_subfolder
            if model_path.is_file():
                model_path = model_path.parent

            args = {}
            if token:
                args["token"] = token
            if repo_type:
                args["repo_type"] = repo_type
            if revision:
                args["revision"] = revision
            args["local_dir"] = model_path
        except Exception as e:
            ino_print_log("InoHuggingFaceDownloadRepo", "", e)
            return io.NodeOutput(False, f"Error: {e}", "", "", "")

        try:
            result = await asyncio.to_thread(snapshot_download, repo_id, **args)
            rel_path = Path(result).relative_to(model_path_base)
            ino_print_log("InoHuggingFaceDownloadRepo", "file downloaded successfully")
            return io.NodeOutput(True, "Successful", model_type, str(result), str(rel_path))
        except Exception as e:
            ino_print_log("InoHuggingFaceDownloadRepo", "", e)
            return io.NodeOutput(False, f"Error: {e}", "", "", "")


class InoCivitaiDownloadModel(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCivitaiDownloadModel",
            display_name="Ino Civitai Download Model",
            category="InoModelHelper",
            description="Downloads a model file from Civitai.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("model_config", default="{}"),
                io.Combo.Input("model_type", options=list(MODEL_TYPES)),
                io.String.Input("model_subfolder", default="flux1dev"),
                io.String.Input("model_version", default=""),
                io.String.Input("token", default="", optional=True),
                io.String.Input("model_id", default="", optional=True),
                io.Int.Input("file_id", default=0, min=0, max=100, step=1, optional=True),
                io.Combo.Input("chunk_size", options=["8", "16", "32", "64"], optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="msg"),
                io.String.Output(display_name="model_type"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="rel_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, model_config, model_type="", model_subfolder="", model_version="", token="", model_id="", file_id=0, chunk_size="8") -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoCivitaiDownloadModel", "Attempt to run but disabled")
            return io.NodeOutput(False, "", "", "", "")

        try:
            if isinstance(model_config, str):
                input_config = InoJsonHelper.string_to_dict(model_config)
                if input_config["success"]:
                    model_config = input_config["data"]

            if isinstance(model_config, dict):
                model_type = model_config.get("model_type", model_type)
                model_subfolder = model_config.get("model_subfolder", model_subfolder)
                model_version = model_config.get("revision", model_version)
                model_id = model_config.get("repo_id", model_id)
                file_id = int(model_config.get("filename", file_id))

            parent_path = Path(folder_paths.get_input_directory()).parent
            model_path_base = parent_path / "models" / model_type
            model_path = model_path_base / model_subfolder
            if model_path.is_file():
                model_path = model_path.parent

            token = os.getenv("CIVITAI_TOKEN")

            civit_client = InoCivitHelper(token=token)

            download_model = await civit_client.download_model(
                model_path=model_path,
                model_id=int(model_id),
                model_version=int(model_version),
                file_id=file_id,
            )
            if ino_is_err(download_model):
                return io.NodeOutput(False, download_model["msg"], model_type, "", "")

            await civit_client.close()

            abs_path = download_model["local_file_path"]
            rel_path = Path(abs_path).relative_to(model_path_base)

            return io.NodeOutput(True, download_model["msg"], model_type, str(abs_path), str(rel_path))
        except Exception as e:
            ino_print_log("InoCivitaiDownloadModel", "", e)
            return io.NodeOutput(False, str(e), "", "", "")


class InoHandleDownloadModel(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoHandleDownloadModel",
            display_name="Ino Handle Download Model",
            category="InoModelHelper",
            description="Delegates model download to the appropriate handler (S3, HuggingFace, or Civitai) based on config.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("config", default="{}"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="msg"),
                io.String.Output(display_name="model_type"),
                io.String.Output(display_name="abs_path"),
                io.String.Output(display_name="rel_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, config) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoHandleDownloadModel", "Attempt to run but disabled")
            return io.NodeOutput(False, "not enabled", "", "", "")

        config_dict = InoJsonHelper.string_to_dict(config)
        if not config_dict["success"]:
            ino_print_log("InoHandleDownloadModel", "invalid config string")
            return io.NodeOutput(False, config_dict["msg"], "", "", "")

        config_dict = config_dict["data"]

        loader = None
        if config_dict["host"] == "s3":
            loader = InoS3DownloadModel()
        elif config_dict["host"] == "hf":
            loader = InoHuggingFaceDownloadModel()
        elif config_dict["host"] == "civitai":
            loader = InoCivitaiDownloadModel()
        else:
            ino_print_log("InoHandleDownloadModel", "unknown host")
            return io.NodeOutput(False, "unknown host", "", "", "")

        result = await loader.execute(enabled=True, model_config=config)
        ino_print_log("InoHandleDownloadModel", "delegated to loader completed")
        return result


LOCAL_NODE_CLASS = {
    "InoCreateModelFileConfig": InoCreateDownloadModelConfig,
    "InoGetImageModelDownloadConfig": InoGetImageModelDownloadConfig,
    "InoGetVideoModelDownloadConfig": InoGetVideoModelDownloadConfig,
    "InoGetVaeDownloadConfig": InoGetVaeDownloadConfig,
    "InoGetClipDownloadConfig": InoGetClipDownloadConfig,
    "InoGetControlnetDownloadConfig": InoGetControlnetDownloadConfig,
    "InoGetLoraDownloadConfig": InoGetLoraDownloadConfig,

    "InoHttpDownloadModel": InoHttpDownloadModel,
    "InoS3DownloadModel": InoS3DownloadModel,
    "InoHuggingFaceDownloadModel": InoHuggingFaceDownloadModel,
    "InoHuggingFaceDownloadRepo": InoHuggingFaceDownloadRepo,
    "InoCivitaiDownloadModel": InoCivitaiDownloadModel,

    "InoHandleDownloadModel": InoHandleDownloadModel,
}
LOCAL_NODE_NAME = {
    "InoCreateModelFileConfig": "Ino Create Model File Config",
    "InoGetImageModelDownloadConfig": "Ino Get Image Model Download Config",
    "InoGetVideoModelDownloadConfig": "Ino Get Video Model Download Config",
    "InoGetVaeDownloadConfig": "Ino Get Vae Download Config",
    "InoGetClipDownloadConfig": "Ino Get Clip Download Config",
    "InoGetControlnetDownloadConfig": "Ino Get Controlnet Download Config",
    "InoGetLoraDownloadConfig": "Ino Get Lora Download Config",

    "InoHttpDownloadModel": "Ino Http Download Model",
    "InoS3DownloadModel": "Ino S3 Download Model",
    "InoHuggingFaceDownloadModel": "Ino Hugging Face Download Model",
    "InoHuggingFaceDownloadRepo": "Ino Hugging Face Download Repo",
    "InoCivitaiDownloadModel": "Ino Civitai Download Model",

    "InoHandleDownloadModel": "Ino Handle Download Model",
}
