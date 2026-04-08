from comfy_api.latest import io


class InoCastAnyToString(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCastAnyToString",
            display_name="Ino Cast Any To String",
            category="InoCastHelper",

            description="Casts any input value to a string.",
            inputs=[
                io.AnyType.Input("input_any"),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_any) -> io.NodeOutput:
        return io.NodeOutput(str(input_any))


class InoCastAnyToInt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCastAnyToInt",
            display_name="Ino Cast Any To Int",
            category="InoCastHelper",
            description="Casts any input value to an integer.",
            inputs=[
                io.AnyType.Input("input_any"),
            ],
            outputs=[
                io.Int.Output(display_name="int"),
            ],
        )

    @classmethod
    def execute(cls, input_any) -> io.NodeOutput:
        return io.NodeOutput(int(input_any))


class InoCastAnyToModel(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCastAnyToModel",
            display_name="Ino Cast Any To Model",
            category="InoCastHelper",
            description="Casts any input to a MODEL type.",
            inputs=[
                io.AnyType.Input("input_any"),
            ],
            outputs=[
                io.Model.Output(display_name="model"),
            ],
        )

    @classmethod
    def execute(cls, input_any) -> io.NodeOutput:
        return io.NodeOutput(input_any)


class InoCastAnyToClip(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCastAnyToClip",
            display_name="Ino Cast Any To Clip",
            category="InoCastHelper",
            description="Casts any input to a CLIP type.",
            inputs=[
                io.AnyType.Input("input_any"),
            ],
            outputs=[
                io.Clip.Output(display_name="clip"),
            ],
        )

    @classmethod
    def execute(cls, input_any) -> io.NodeOutput:
        return io.NodeOutput(input_any)


class InoCastAnyToVae(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCastAnyToVae",
            display_name="Ino Cast Any To Vae",
            category="InoCastHelper",
            description="Casts any input to a VAE type.",
            inputs=[
                io.AnyType.Input("input_any"),
            ],
            outputs=[
                io.Vae.Output(display_name="vae"),
            ],
        )

    @classmethod
    def execute(cls, input_any) -> io.NodeOutput:
        return io.NodeOutput(input_any)


class InoCastAnyToControlnet(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCastAnyToControlnet",
            display_name="Ino Cast Any To Controlnet",
            category="InoCastHelper",
            description="Casts any input to a CONTROL_NET type.",
            inputs=[
                io.AnyType.Input("input_any"),
            ],
            outputs=[
                io.ControlNet.Output(display_name="control_net"),
            ],
        )

    @classmethod
    def execute(cls, input_any) -> io.NodeOutput:
        return io.NodeOutput(input_any)


class InoCastStringToCombo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCastStringToCombo",
            display_name="Ino Cast String To Combo",
            category="InoCastHelper",
            description="Converts a string to a combo-compatible output. Wire this into any combo input (e.g. parent_folder).",
            inputs=[
                io.String.Input("input_string", default=""),
            ],
            outputs=[
                io.AnyType.Output(display_name="combo"),
            ],
        )

    @classmethod
    def execute(cls, input_string) -> io.NodeOutput:
        return io.NodeOutput(input_string)


LOCAL_NODE_CLASS = {
    "InoCastAnyToString": InoCastAnyToString,
    "InoCastAnyToInt": InoCastAnyToInt,
    "InoCastAnyToModel": InoCastAnyToModel,
    "InoCastAnyToClip": InoCastAnyToClip,
    "InoCastAnyToVae": InoCastAnyToVae,
    "InoCastAnyToControlnet": InoCastAnyToControlnet,
    "InoCastStringToCombo": InoCastStringToCombo,
}
LOCAL_NODE_NAME = {
    "InoCastAnyToString": "Ino Cast Any To String",
    "InoCastAnyToInt": "Ino Cast Any To Int",
    "InoCastAnyToModel": "Ino Cast Any To Model",
    "InoCastAnyToClip": "Ino Cast Any To Clip",
    "InoCastAnyToVae": "Ino Cast Any To Vae",
    "InoCastAnyToControlnet": "Ino Cast Any To Controlnet",
    "InoCastStringToCombo": "Ino Cast String To Combo",
}
