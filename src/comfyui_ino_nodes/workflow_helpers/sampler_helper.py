from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone

from inopyutils import InoJsonHelper

from comfy.samplers import SAMPLER_NAMES, SCHEDULER_NAMES
from comfy_api.latest import io

from .download_model_helper import InoHandleDownloadModel
from ..node_helper import ino_print_log

default_bool = ["unset", "true", "false"]
sampler_names = ["unset"] + SAMPLER_NAMES
scheduler_names = ["unset"] + SCHEDULER_NAMES


def _load_models(config: str = "default", model_type: str = "models") -> dict:
    if config == "default":
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        json_path = base_dir / "data" / f"{model_type}.json"
        read_json = InoJsonHelper.read_json_from_file_sync(file_path=str(json_path.resolve()))
        if not read_json["success"]:
            ino_print_log("_load_models", "read_json failed")
            return read_json
        json_data = read_json["data"]
    else:
        json_data = InoJsonHelper.string_to_dict(json_string=config)
        if not json_data["success"]:
            ino_print_log("_load_models", "string_to_dict failed")
            return json_data
        json_data = json_data["data"]

    json_data = json_data[model_type]
    names = [m["name"] for m in json_data]
    ids = [m["id"] for m in json_data]

    ino_print_log("_load_models", "success")
    return {"success": True, "msg": "success", "names": names, "ids": ids, "fields": json_data}


def get_model_by_field(models, field_name, field_match):
    for m in models:
        if m[field_name] == field_match:
            ino_print_log("get_model_by_field", "match found")
            return deepcopy(m)
    ino_print_log("get_model_by_field", "no match found")
    return {}


def prepare_lora_config(lora_config: str) -> dict:
    load_json = InoJsonHelper.string_to_dict(json_string=lora_config)
    if not load_json["success"]:
        ino_print_log("prepare_lora_config", "string_to_dict failed")
        return {"use_lora": False, "lora_config": None}
    ino_print_log("prepare_lora_config", "success")
    return {"use_lora": True, "lora_config": load_json["data"]}


async def load_lora(config_str, model, clip):
    prepared_config = prepare_lora_config(config_str)
    if not prepared_config["use_lora"]:
        ino_print_log("load_lora", "use_lora is False")
        return False, model, clip, ""

    config_dict = prepared_config["lora_config"]

    lora_file_loader = await InoHandleDownloadModel.execute(
        enabled=True,
        config=InoJsonHelper.dict_to_string(config_dict["file"])["data"],
    )
    if not lora_file_loader.args[0]:
        ino_print_log("load_lora", "lora_file_loader failed")
        return False, model, clip, ""

    from nodes import LoraLoader
    lora_loader = LoraLoader()
    lora_loaded = lora_loader.load_lora(
        model=model, clip=clip,
        lora_name=lora_file_loader.args[4],
        strength_model=config_dict["strength_model"],
        strength_clip=config_dict["strength_clip"]
    )
    ino_print_log("load_lora", "lora loaded")
    return True, lora_loaded[0], lora_loaded[1], f"{config_dict['trigger_word']}, "


class InoGetModelConfig(io.ComfyNode):
    @staticmethod
    def load_models():
        load = _load_models()
        if load["success"]:
            names = ["unset"] + load["names"]
            return {"success": load["msg"], "msg": "", "names": names, "ids": load["ids"], "fields": load["fields"]}
        return None

    @classmethod
    def define_schema(cls):
        models = cls.load_models()
        return io.Schema(
            node_id="InoGetModelConfig",
            display_name="Ino Get Model Config",
            category="InoSamplerHelper",
            description="Retrieves a model configuration by name or ID from the models JSON.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("model_name", options=models["names"], tooltip="The name of the Model."),
                io.Combo.Input("model_id", options=models["ids"], tooltip="The id of the Model."),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.Int.Output(display_name="model_id"),
                io.String.Output(display_name="model_name"),
                io.String.Output(display_name="model_config"),
                io.String.Output(display_name="datetime_iso"),
            ],
        )

    @classmethod
    def execute(cls, enabled, model_name, model_id) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoGetModelConfig", "not enabled")
            return io.NodeOutput(False, "not enabled", -1, "", "", "")

        time_now = datetime.now(timezone.utc).isoformat()

        models = cls.load_models()["fields"]
        if model_name == "unset":
            model_cfg = get_model_by_field(models, "id", model_id)
        else:
            model_cfg = get_model_by_field(models, "name", model_name)

        model_cfg_str = InoJsonHelper.dict_to_string(model_cfg)
        if not model_cfg_str["success"]:
            ino_print_log("InoGetModelConfig", "dict_to_string failed")
            return io.NodeOutput(model_cfg_str["success"], model_cfg_str["msg"], -1, "", "", time_now)

        ino_print_log("InoGetModelConfig", "success")
        return io.NodeOutput(True, "Success", model_cfg["id"], model_cfg["name"], model_cfg_str["data"], time_now)


class InoGetLoraConfig(io.ComfyNode):
    @staticmethod
    def load_models():
        load = _load_models("default", "loras")
        if load["success"]:
            names = ["unset"] + load["names"]
            return {"success": load["msg"], "msg": "", "names": names, "ids": load["ids"], "fields": load["fields"]}
        return None

    @classmethod
    def define_schema(cls):
        models = cls.load_models()
        return io.Schema(
            node_id="InoGetLoraConfig",
            display_name="Ino Get Lora Config",
            category="InoSamplerHelper",
            description="Retrieves a LoRA configuration by name or ID from the loras JSON.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Combo.Input("lora_name", options=models["names"], tooltip="The name of the LoRA."),
                io.Combo.Input("lora_id", options=models["ids"], tooltip="The id of the LoRA."),
                io.Float.Input("strength_model", default=-1.0, min=-1.0, max=1.0, step=0.01, optional=True),
                io.Float.Input("strength_clip", default=-1.0, min=-1.0, max=1.0, step=0.01, optional=True),
            ],
            outputs=[
                io.Int.Output(display_name="lora_id"),
                io.String.Output(display_name="lora_name"),
                io.String.Output(display_name="lora_config"),
            ],
        )

    @classmethod
    def execute(cls, enabled, lora_name, lora_id, strength_model=-1.0, strength_clip=-1.0) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoGetLoraConfig", "not enabled")
            return io.NodeOutput(-1, "", "")

        models = cls.load_models()["fields"]
        if lora_name == "unset":
            lora_cfg = get_model_by_field(models, "id", lora_id)
        else:
            lora_cfg = get_model_by_field(models, "name", lora_name)

        if strength_model != -1:
            lora_cfg["strength_model"] = strength_model
        if strength_clip != -1:
            lora_cfg["strength_clip"] = strength_clip

        lora_cfg_str = InoJsonHelper.dict_to_string(lora_cfg)
        if not lora_cfg_str["success"]:
            ino_print_log("InoGetLoraConfig", "dict_to_string failed")
            return io.NodeOutput(-1, "", "")

        ino_print_log("InoGetLoraConfig", "success")
        return io.NodeOutput(lora_cfg["id"], lora_cfg["name"], lora_cfg_str["data"])


class InoCreateLoraConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCreateLoraConfig",
            display_name="Ino Create Lora Config",
            category="InoSamplerHelper",
            description="Creates a LoRA configuration JSON from individual fields.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("lora_id", tooltip="The id of the Model."),
                io.String.Input("lora_name", tooltip="The name of the Model."),
                io.String.Input("trigger_word", default="trigger"),
                io.String.Input("base_model", default="flux1dev"),
                io.String.Input("file", default="", tooltip="it should be a json string"),
                io.String.Input("lora_type", default="person", optional=True),
                io.String.Input("weight_type", default="fp16", optional=True),
                io.String.Input("trigger_words", default="trigger1,trigger2", optional=True),
                io.String.Input("description", default="", optional=True),
                io.String.Input("tags", default="style, instagram", optional=True),
                io.Float.Input("strength_model", default=0.9, min=-1.0, max=1.0, step=0.01, optional=True),
                io.Float.Input("strength_clip", default=0.9, min=-1.0, max=1.0, step=0.01, optional=True),
            ],
            outputs=[
                io.Int.Output(display_name="lora_id"),
                io.String.Output(display_name="lora_name"),
                io.String.Output(display_name="lora_config"),
            ],
        )

    @classmethod
    def execute(cls, enabled, lora_id, lora_name, trigger_word, base_model, file,
                lora_type="person", weight_type="fp16", trigger_words="", description="", tags="",
                strength_model=0.9, strength_clip=0.9) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoCreateLoraConfig", "not enabled")
            return io.NodeOutput(-1, "", "")

        file_dict = InoJsonHelper.string_to_dict(file)
        if not file_dict["success"]:
            ino_print_log("InoCreateLoraConfig", "failed to parse file")
            return io.NodeOutput(-1, "failed to parse file", "")
        file_dict = file_dict["data"]

        lora_config = {
            "id": lora_id, "name": lora_name, "base_model": base_model, "type": lora_type,
            "trigger_word": trigger_word, "trigger_words": trigger_words, "file": file_dict,
            "weight_type": weight_type, "strength_model": strength_model, "strength_clip": strength_clip,
            "description": description, "tags": tags,
        }
        lora_config_str = InoJsonHelper.dict_to_string(lora_config)["data"]

        ino_print_log("InoCreateLoraConfig", "success")
        return io.NodeOutput(lora_config["id"], lora_config["name"], lora_config_str)


class InoShowModelConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoShowModelConfig",
            display_name="Ino Show Model Config",
            category="InoSamplerHelper",
            description="Parses a model config JSON string and outputs all individual fields.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("config", multiline=True),
            ],
            outputs=[
                io.String.Output(display_name="name"), io.String.Output(display_name="type"),
                io.String.Output(display_name="unet"), io.String.Output(display_name="weight_type"),
                io.Boolean.Output(display_name="use_dual_clip"), io.Boolean.Output(display_name="use_flux_encoder"),
                io.Boolean.Output(display_name="use_flux_guidance"), io.Float.Output(display_name="guidance"),
                io.Boolean.Output(display_name="use_negative_prompt"),
                io.String.Output(display_name="clip1"), io.String.Output(display_name="clip2"),
                io.String.Output(display_name="vae"),
                io.Boolean.Output(display_name="use_cfg"), io.Int.Output(display_name="cfg"),
                io.String.Output(display_name="sampler_name"), io.String.Output(display_name="scheduler_name"),
                io.Int.Output(display_name="steps"), io.Int.Output(display_name="denoise"),
                io.String.Output(display_name="tags"), io.String.Output(display_name="description"),
                io.String.Output(display_name="lora_compatible"),
            ],
        )

    @classmethod
    def execute(cls, enabled, config) -> io.NodeOutput:
        empty = io.NodeOutput("", "", "", "", False, False, False, 0.0, False, "", "", "", False, 0, "", "", 0, 0, "", "", "")
        if not enabled:
            ino_print_log("InoShowModelConfig", "not enabled")
            return empty

        load_json = InoJsonHelper.string_to_dict(config)
        if not load_json["success"]:
            ino_print_log("InoShowModelConfig", "string_to_dict failed")
            return empty
        c = load_json["data"]

        ino_print_log("InoShowModelConfig", "success")
        return io.NodeOutput(
            c["name"], c["type"], c["unet"], c["weight_type"],
            c["use_dual_clip"], c["use_flux_encoder"], c["use_flux_guidance"], c["guidance"],
            c["use_negative_prompt"], c["clip1"], c["clip2"], c["vae"],
            c["use_cfg"], c["cfg"], c["sampler_name"], c["scheduler_name"],
            c["steps"], c["denoise"], c["tags"], c["description"], c["lora_compatible"],
        )


class InoUpdateModelConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoUpdateModelConfig",
            display_name="Ino Update Model Config",
            category="InoSamplerHelper",
            description="Overrides specific fields in a model config JSON. Unset values are left unchanged.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("config", multiline=True),
                io.Combo.Input("use_dual_clip", options=default_bool, optional=True),
                io.Combo.Input("use_flux_encoder", options=default_bool, optional=True),
                io.Combo.Input("use_flux_guidance", options=default_bool, optional=True),
                io.Float.Input("guidance", default=-1.0, min=-1.0, max=100.0, optional=True),
                io.Combo.Input("use_negative_prompt", options=default_bool, optional=True),
                io.Combo.Input("use_cfg", options=default_bool, optional=True),
                io.Float.Input("cfg", default=-1.0, min=-1.0, max=100.0, optional=True),
                io.Combo.Input("sampler_name", options=sampler_names, optional=True),
                io.Combo.Input("scheduler_name", options=scheduler_names, optional=True),
                io.Int.Input("steps", default=-1, min=-1, max=100, optional=True),
                io.Float.Input("denoise", default=-1.0, min=-1.0, max=1.0, step=0.01, optional=True),
            ],
            outputs=[
                io.String.Output(display_name="old_config"),
                io.String.Output(display_name="new_config"),
            ],
        )

    @classmethod
    def execute(cls, enabled, config, use_dual_clip="unset", use_flux_encoder="unset", use_flux_guidance="unset",
                guidance=-1.0, use_negative_prompt="unset", use_cfg="unset", cfg=-1.0,
                sampler_name="unset", scheduler_name="unset", steps=-1, denoise=-1.0) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoUpdateModelConfig", "not enabled")
            return io.NodeOutput("", "")

        load_json = InoJsonHelper.string_to_dict(config)
        if not load_json["success"]:
            ino_print_log("InoUpdateModelConfig", "string_to_dict failed")
            return io.NodeOutput(config, "")
        model_cfg = load_json["data"]

        if use_dual_clip != "unset": model_cfg["use_dual_clip"] = use_dual_clip
        if use_flux_encoder != "unset": model_cfg["use_flux_encoder"] = use_flux_encoder
        if use_flux_guidance != "unset": model_cfg["use_flux_guidance"] = use_flux_guidance
        if guidance != -1: model_cfg["guidance"] = guidance
        if use_negative_prompt != "unset": model_cfg["use_negative_prompt"] = use_negative_prompt
        if use_cfg != "unset": model_cfg["use_cfg"] = use_cfg
        if cfg != -1: model_cfg["cfg"] = cfg
        if sampler_name != "unset": model_cfg["sampler_name"] = sampler_name
        if scheduler_name != "unset": model_cfg["scheduler_name"] = scheduler_name
        if steps != -1: model_cfg["steps"] = steps
        if denoise != -1: model_cfg["denoise"] = denoise

        model_cfg_str = InoJsonHelper.dict_to_string(model_cfg)
        if not model_cfg_str["success"]:
            ino_print_log("InoUpdateModelConfig", "dict_to_string failed")
            return io.NodeOutput(config, "")

        ino_print_log("InoUpdateModelConfig", "success")
        return io.NodeOutput(config, model_cfg_str["data"])


class InoShowLoraConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoShowLoraConfig",
            display_name="Ino Show Lora Config",
            category="InoSamplerHelper",
            description="Parses a LoRA config JSON string and outputs all individual fields.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("config", multiline=True),
            ],
            outputs=[
                io.String.Output(display_name="name"), io.String.Output(display_name="base_model"),
                io.String.Output(display_name="type"), io.String.Output(display_name="trigger_word"),
                io.String.Output(display_name="trigger_words"), io.String.Output(display_name="file"),
                io.String.Output(display_name="weight_type"),
                io.Float.Output(display_name="model_strength"), io.Float.Output(display_name="clip_strength"),
                io.String.Output(display_name="description"), io.String.Output(display_name="tags"),
            ],
        )

    @classmethod
    def execute(cls, enabled, config) -> io.NodeOutput:
        empty = io.NodeOutput("", "", "", "", "", "", "", 0.0, 0.0, "", "")
        if not enabled:
            ino_print_log("InoShowLoraConfig", "not enabled")
            return empty

        load_json = InoJsonHelper.string_to_dict(config)
        if not load_json["success"]:
            ino_print_log("InoShowLoraConfig", "string_to_dict failed")
            return empty
        c = load_json["data"]

        ino_print_log("InoShowLoraConfig", "success")
        return io.NodeOutput(
            c["name"], c["base_model"], c["type"], c["trigger_word"], c["trigger_words"],
            str(c["file"]), c["weight_type"], c["strength_model"], c["strength_clip"],
            c["description"], c["tags"],
        )


class InoLoadSamplerModels(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoLoadSamplerModels",
            display_name="Ino Load Sampler Models",
            category="InoSamplerHelper",
            description="Downloads and loads all sampler models (UNET, CLIP, VAE) and up to 4 LoRAs from config.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("model_config"),
                io.String.Input("lora_1_config"),
                io.String.Input("lora_2_config"),
                io.String.Input("lora_3_config"),
                io.String.Input("lora_4_config"),
                io.Combo.Input("clip_device", options=["default", "cpu"], optional=True, advanced=True),
                io.Combo.Input("use_dual_clip", options=default_bool, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.Model.Output(display_name="model"),
                io.Clip.Output(display_name="clip"),
                io.Vae.Output(display_name="vae"),
                io.Boolean.Output(display_name="lora_applied"),
                io.String.Output(display_name="trigger_words"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, model_config,
                      lora_1_config, lora_2_config, lora_3_config, lora_4_config,
                      clip_device="default", use_dual_clip="unset") -> io.NodeOutput:
        fail = lambda msg: io.NodeOutput(False, msg, None, None, None, None, None)

        if not enabled:
            ino_print_log("InoLoadSamplerModels", "not enabled")
            return fail("not enabled")

        try:
            load_json = InoJsonHelper.string_to_dict(model_config)
            if not load_json["success"]:
                ino_print_log("InoLoadSamplerModels", "load_json failed")
                return fail(load_json["msg"])

            model_cfg = load_json["data"]

            unet_cfg = InoJsonHelper.dict_to_string(model_cfg["unet"])["data"]
            clip1_cfg = InoJsonHelper.dict_to_string(model_cfg["clip1"])["data"]
            clip2_cfg = InoJsonHelper.dict_to_string(model_cfg["clip2"])["data"]
            vae_cfg = InoJsonHelper.dict_to_string(model_cfg["vae"])["data"]

            unet_r = await InoHandleDownloadModel.execute(enabled=True, config=unet_cfg)
            if not unet_r.args[0]: return fail(unet_r.args[1])

            clip1_r = await InoHandleDownloadModel.execute(enabled=True, config=clip1_cfg)
            if not clip1_r.args[0]: return fail(clip1_r.args[1])

            clip2_r = await InoHandleDownloadModel.execute(enabled=True, config=clip2_cfg)
            if not clip2_r.args[0]: return fail(clip2_r.args[1])

            vae_r = await InoHandleDownloadModel.execute(enabled=True, config=vae_cfg)
            if not vae_r.args[0]: return fail(vae_r.args[1])

            from nodes import UNETLoader, CLIPLoader, DualCLIPLoader, VAELoader

            load_unet = UNETLoader().load_unet(unet_name=unet_r.args[4], weight_dtype=model_cfg["weight_type"])

            dual_clip = model_cfg["use_dual_clip"]
            if dual_clip:
                load_clip = DualCLIPLoader().load_clip(
                    clip_name1=clip1_r.args[4], clip_name2=clip2_r.args[4],
                    type=model_cfg["type"], device=clip_device,
                )
            else:
                load_clip = CLIPLoader().load_clip(
                    clip_name=clip1_r.args[4], type=model_cfg["type"], device=clip_device,
                )

            load_vae = VAELoader().load_vae(vae_name=vae_r.args[4])

            model_loaded = load_unet[0]
            clip_loaded = load_clip[0]
            trigger_words = ""
            lora_loaded = False

            for lora_cfg in [lora_1_config, lora_2_config, lora_3_config, lora_4_config]:
                result = await load_lora(lora_cfg, model_loaded, clip_loaded)
                model_loaded = result[1]
                clip_loaded = result[2]
                trigger_words += result[3]
                if result[0]:
                    lora_loaded = True

            ino_print_log("InoLoadSamplerModels", "Success")
            return io.NodeOutput(True, "Success", model_loaded, clip_loaded, load_vae[0], lora_loaded, trigger_words)
        except Exception as e:
            ino_print_log("InoLoadSamplerModels", str(e))
            return fail(str(e))


class InoGetSamplerConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetSamplerConfig",
            display_name="Ino Get Sampler Config",
            category="InoSamplerHelper",
            description="Builds guider, sampler, and sigmas from a model config with optional overrides.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("config", multiline=True, default=""),
                io.Model.Input("model"),
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Combo.Input("use_cfg", options=default_bool, optional=True),
                io.Float.Input("cfg", default=-1.0, min=-1.0, max=100.0, optional=True),
                io.Combo.Input("sampler_name", options=sampler_names, optional=True),
                io.Combo.Input("scheduler_name", options=scheduler_names, optional=True),
                io.Int.Input("steps", default=-1, min=-1, max=100, optional=True),
                io.Float.Input("denoise", default=-1.0, min=-1.0, max=1.0, step=0.01, optional=True),
            ],
            outputs=[
                io.Guider.Output(display_name="guider"),
                io.Sampler.Output(display_name="sampler"),
                io.Sigmas.Output(display_name="sigmas"),
                io.String.Output(display_name="old_config"),
                io.String.Output(display_name="new_config"),
            ],
        )

    @classmethod
    def execute(cls, enabled, config, model, positive, negative,
                use_cfg="unset", cfg=-1.0, sampler_name="unset", scheduler_name="unset",
                steps=-1, denoise=-1.0) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoGetSamplerConfig", "not enabled")
            return io.NodeOutput(None, None, None, "", "")

        updated = InoUpdateModelConfig.execute(
            enabled=True, config=config, use_cfg=use_cfg, cfg=cfg,
            sampler_name=sampler_name, scheduler_name=scheduler_name, steps=steps, denoise=denoise
        )

        load_json = InoJsonHelper.string_to_dict(updated.args[1])
        if not load_json["success"]:
            ino_print_log("InoGetSamplerConfig", "string_to_dict failed")
            return io.NodeOutput(None, None, None, "", "")

        model_cfg = load_json["data"]
        use_cfg_val = bool(model_cfg.get("use_cfg", False))

        from comfy_extras.nodes_custom_sampler import BasicGuider, CFGGuider, KSamplerSelect, BasicScheduler

        if use_cfg_val:
            get_guider = CFGGuider().get_guider(model=model, positive=positive, negative=negative, cfg=model_cfg.get("cfg", -1))
        else:
            get_guider = BasicGuider().get_guider(model=model, conditioning=positive)

        get_sampler = KSamplerSelect().get_sampler(sampler_name=model_cfg.get("sampler_name", "none"))
        get_sigmas = BasicScheduler().get_sigmas(
            model=model, scheduler=model_cfg.get("scheduler_name", "none"),
            steps=model_cfg.get("steps", -1), denoise=model_cfg.get("denoise", -1),
        )

        model_cfg_str = InoJsonHelper.dict_to_string(model_cfg)
        if not model_cfg_str["success"]:
            ino_print_log("InoGetSamplerConfig", "dict_to_string failed")
            return io.NodeOutput(None, None, None, config, "")

        ino_print_log("InoGetSamplerConfig", "success")
        return io.NodeOutput(get_guider[0], get_sampler[0], get_sigmas[0], config, model_cfg_str["data"])


class InoGetConditioning(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetConditioning",
            display_name="Ino Get Conditioning",
            category="InoSamplerHelper",
            description="Encodes positive and negative conditioning from text using CLIP, with optional Flux encoder and guidance.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("config", multiline=True, default=""),
                io.Clip.Input("clip"),
                io.String.Input("positive1", multiline=True, default=""),
                io.String.Input("positive2", multiline=True, default=""),
                io.String.Input("negative", multiline=True, default=""),
                io.Combo.Input("use_flux_encoder", options=default_bool, optional=True),
                io.Combo.Input("use_flux_guidance", options=default_bool, optional=True),
                io.Float.Input("guidance", default=-1.0, min=-1.0, max=100.0, optional=True),
                io.Combo.Input("use_negative_prompt", options=default_bool, optional=True),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.String.Output(display_name="old_config"),
                io.String.Output(display_name="new_config"),
            ],
        )

    @classmethod
    def execute(cls, enabled, config, clip, positive1, positive2, negative,
                use_flux_encoder="unset", use_flux_guidance="unset", guidance=-1.0,
                use_negative_prompt="unset") -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoGetConditioning", "not enabled")
            return io.NodeOutput(None, None, "", "")

        updated = InoUpdateModelConfig.execute(
            enabled=True, config=config,
            use_flux_encoder=use_flux_encoder, use_flux_guidance=use_flux_guidance,
            guidance=guidance, use_negative_prompt=use_negative_prompt
        )

        load_json = InoJsonHelper.string_to_dict(updated.args[1])
        if not load_json["success"]:
            ino_print_log("InoGetConditioning", "string_to_dict failed")
            return io.NodeOutput(None, None, "", "")

        model_cfg = load_json["data"]
        final_guidance = float(model_cfg.get("guidance", -1))
        use_neg = bool(model_cfg.get("use_negative_prompt", False))
        use_flux = bool(model_cfg.get("use_flux_encoder", False))
        use_flux_guid = bool(model_cfg.get("use_flux_guidance", False))

        from nodes import CLIPTextEncode, ConditioningZeroOut
        from comfy_extras.nodes_flux import CLIPTextEncodeFlux, FluxGuidance

        if use_flux:
            positive_condition = CLIPTextEncodeFlux().encode(clip=clip, clip_l=positive1, t5xxl=positive2, guidance=final_guidance)
        else:
            positive_condition = CLIPTextEncode().encode(clip=clip, text=positive1)

        if not use_flux and use_flux_guid:
            positive_condition = FluxGuidance().append(conditioning=positive_condition[0], guidance=final_guidance)

        if use_neg:
            negative_condition = CLIPTextEncode().encode(clip=clip, text=negative)
        else:
            negative_condition = ConditioningZeroOut().zero_out(conditioning=positive_condition[0])

        model_cfg_str = InoJsonHelper.dict_to_string(model_cfg)
        if not model_cfg_str["success"]:
            ino_print_log("InoGetConditioning", "dict_to_string failed")
            return io.NodeOutput(None, None, config, "")

        ino_print_log("InoGetConditioning", "success")
        return io.NodeOutput(positive_condition[0], negative_condition[0], config, model_cfg_str["data"])


class InoGetModelDownloadConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoGetModelDownloadConfig",
            display_name="Ino Get Model Download Config",
            category="InoSamplerHelper",
            description="Extracts individual download configs (UNET, CLIP1, CLIP2, VAE) from a model config.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("config", multiline=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="unet"),
                io.String.Output(display_name="clip1"),
                io.String.Output(display_name="clip2"),
                io.String.Output(display_name="vae"),
            ],
        )

    @classmethod
    def execute(cls, enabled, config) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoGetModelDownloadConfig", "not enabled")
            return io.NodeOutput(False, "", "", "", "")

        load_json = InoJsonHelper.string_to_dict(config)
        if not load_json["success"]:
            ino_print_log("InoGetModelDownloadConfig", "string_to_dict failed")
            return io.NodeOutput(False, "", "", "", "")

        model_cfg = load_json["data"]
        ino_print_log("InoGetModelDownloadConfig", "success")
        return io.NodeOutput(
            True,
            InoJsonHelper.dict_to_string(model_cfg["unet"])["data"],
            InoJsonHelper.dict_to_string(model_cfg["clip1"])["data"],
            InoJsonHelper.dict_to_string(model_cfg["clip2"])["data"],
            InoJsonHelper.dict_to_string(model_cfg["vae"])["data"],
        )


LOCAL_NODE_CLASS = {
    "InoGetModelConfig": InoGetModelConfig,
    "InoShowModelConfig": InoShowModelConfig,
    "InoUpdateModelConfig": InoUpdateModelConfig,
    "InoGetLoraConfig": InoGetLoraConfig,
    "InoCreateLoraConfig": InoCreateLoraConfig,
    "InoShowLoraConfig": InoShowLoraConfig,
    "InoLoadSamplerModels": InoLoadSamplerModels,
    "InoGetConditioning": InoGetConditioning,
    "InoGetSamplerConfig": InoGetSamplerConfig,
    "InoGetModelDownloadConfig": InoGetModelDownloadConfig,
}
LOCAL_NODE_NAME = {
    "InoGetModelConfig": "Ino Get Model Config",
    "InoShowModelConfig": "Ino Show Model Config",
    "InoUpdateModelConfig": "Ino Update Model Config",
    "InoGetLoraConfig": "Ino Get Lora Config",
    "InoCreateLoraConfig": "Ino Create Lora Config",
    "InoShowLoraConfig": "Ino Show Lora Config",
    "InoLoadSamplerModels": "Ino Load Sampler Models",
    "InoGetConditioning": "Ino Get Conditioning",
    "InoGetSamplerConfig": "Ino Get Sampler Config",
    "InoGetModelDownloadConfig": "Ino Get Model Download Config",
}
