from pathlib import Path

from inopyutils import InoJsonHelper

from comfy_api.latest import io

from ..node_helper import ino_print_log, PARENT_FOLDER_OPTIONS, resolve_comfy_path


class InoJsonSetField(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoJsonSetField",
            display_name="Ino Json Set Field",
            category="InoJsonHelper",
            description="Sets a field in a JSON string and returns the updated JSON.",
            inputs=[
                io.String.Input("base_json", default="{}"),
                io.String.Input("field_name", default=""),
                io.AnyType.Input("field_value"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="json"),
            ],
        )

    @classmethod
    def execute(cls, base_json, field_name, field_value) -> io.NodeOutput:
        try:
            json_object = InoJsonHelper.string_to_dict(base_json)
            if not json_object["success"]:
                ino_print_log("InoJsonSetField", json_object["msg"])
                return io.NodeOutput(False, json_object["msg"], "")
            json_object = json_object["data"]

            json_object[field_name] = field_value
            json_string = InoJsonHelper.dict_to_string(json_object)
            if not json_string["success"]:
                ino_print_log("InoJsonSetField", json_string["msg"])
                return io.NodeOutput(False, json_string["msg"], "")

            ino_print_log("InoJsonSetField", "Success")
            return io.NodeOutput(True, "Success", json_string["data"])
        except Exception as e:
            ino_print_log("InoJsonSetField", "", str(e))
            return io.NodeOutput(False, f"failed: {e}", "")


class InoJsonGetField(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoJsonGetField",
            display_name="Ino Json Get Field",
            category="InoJsonHelper",
            description="Gets a field value from a JSON string by field name.",
            inputs=[
                io.String.Input("base_json", default="{}"),
                io.String.Input("field_name", default=""),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.AnyType.Output(display_name="field_value"),
            ],
        )

    @classmethod
    def execute(cls, base_json, field_name) -> io.NodeOutput:
        try:
            json_object = InoJsonHelper.string_to_dict(base_json)
            if not json_object["success"]:
                ino_print_log("InoJsonGetField", json_object["msg"])
                return io.NodeOutput(False, json_object["msg"], None)
            json_object = json_object["data"]

            ino_print_log("InoJsonGetField", "Success")
            return io.NodeOutput(True, "Success", json_object[field_name])
        except Exception as e:
            ino_print_log("InoJsonGetField", "", str(e))
            return io.NodeOutput(False, f"failed: {e}", None)


class InoSaveJson(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoSaveJson",
            display_name="Ino Save Json",
            category="InoJsonHelper",
            description="Saves a JSON string to a file in the specified folder.",
            is_output_node=True,
            inputs=[
                io.AnyType.Input("execute", optional=True),
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("json_string", default="{}"),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default="data.json"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, json_string, parent_folder, folder, filename, execute=None) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(True, "skipped: not enabled", "", "")
        if execute is not None and not execute:
            return io.NodeOutput(True, "skipped: execute is false", "", "")

        try:
            rel_path, abs_path = resolve_comfy_path(parent_folder, folder, filename)

            Path(abs_path).parent.mkdir(parents=True, exist_ok=True)

            save_json = await InoJsonHelper.save_string_as_json_async(
                json_string=json_string, file_path=abs_path
            )

            if not save_json["success"]:
                ino_print_log("InoSaveJson", save_json["msg"])
                return io.NodeOutput(False, save_json["msg"], rel_path, abs_path)

            ino_print_log("InoSaveJson", "Success")
            return io.NodeOutput(True, save_json["msg"], rel_path, abs_path)
        except Exception as e:
            ino_print_log("InoSaveJson", "", str(e))
            return io.NodeOutput(False, f"failed: {e}", "", "")


LOCAL_NODE_CLASS = {
    "InoJsonSetField": InoJsonSetField,
    "InoJsonGetField": InoJsonGetField,
    "InoSaveJson": InoSaveJson,
}
LOCAL_NODE_NAME = {
    "InoJsonSetField": "Ino Json Set Field",
    "InoJsonGetField": "Ino Json Get Field",
    "InoSaveJson": "Ino Save Json",
}
