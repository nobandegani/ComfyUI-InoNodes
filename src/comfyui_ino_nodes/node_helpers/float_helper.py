import math

from comfy_api.latest import io


class InoFloatToInt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoFloatToInt",
            display_name="Ino Float To Int",
            category="InoFloatHelper",
            description="Converts a float to an integer using round, floor, or ceil.",
            inputs=[
                io.Float.Input("input_float", default=0.0),
                io.Combo.Input("method", options=["round", "floor", "ceil"]),
            ],
            outputs=[
                io.Int.Output(display_name="int"),
            ],
        )

    @classmethod
    def execute(cls, input_float, method) -> io.NodeOutput:
        if method == "round":
            return io.NodeOutput(round(input_float))
        elif method == "floor":
            return io.NodeOutput(math.floor(input_float))
        else:
            return io.NodeOutput(math.ceil(input_float))


class InoCompareFloat(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCompareFloat",
            display_name="Ino Compare Float",
            category="InoFloatHelper",
            description="Compares two float values using a selected operator.",
            inputs=[
                io.Float.Input("float_a", default=0.0),
                io.Float.Input("float_b", default=0.0),
                io.Combo.Input("compare", options=["=", "<", ">", "<=", ">=", "<>"]),
            ],
            outputs=[
                io.Boolean.Output()
            ]
        )

    @classmethod
    def execute(cls, float_a, float_b, compare) -> io.NodeOutput:
        ops = {
            "=": float_a == float_b,
            "<": float_a < float_b,
            ">": float_a > float_b,
            "<=": float_a <= float_b,
            ">=": float_a >= float_b,
            "<>": float_a != float_b,
        }
        return io.NodeOutput(ops[compare])

class InoMathFloat(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoMathFloat",
            display_name="Ino Math Float",
            category="InoFloatHelper",
            description="Performs a math operation on two floats: add, subtract, multiply, divide, modulo, power.",
            inputs=[
                io.Float.Input("float_a", default=0.0),
                io.Float.Input("float_b", default=0.0),
                io.Combo.Input("operation", options=["add", "subtract", "multiply", "divide", "modulo", "power"]),
            ],
            outputs=[
                io.Float.Output(display_name="float"),
                io.Int.Output(display_name="int"),
            ],
        )

    @classmethod
    def execute(cls, float_a, float_b, operation) -> io.NodeOutput:
        if operation == "add":
            r = float_a + float_b
        elif operation == "subtract":
            r = float_a - float_b
        elif operation == "multiply":
            r = float_a * float_b
        elif operation == "divide":
            r = float_a / float_b if float_b != 0 else 0.0
        elif operation == "modulo":
            r = math.fmod(float_a, float_b) if float_b != 0 else 0.0
        else:
            r = float_a ** float_b
        return io.NodeOutput(float(r), int(r))


LOCAL_NODE_CLASS = {
    "InoFloatToInt": InoFloatToInt,
    "InoCompareFloat": InoCompareFloat,
    "InoMathFloat": InoMathFloat,
}
LOCAL_NODE_NAME = {
    "InoFloatToInt": "Ino Float To Int",
    "InoCompareFloat": "Ino Compare Float",
    "InoMathFloat": "Ino Math Float",
}
