import random
from comfy_api.latest import io


class InoRandomIntInRange(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoRandomIntInRange",
            display_name="Ino Random Int In Range",
            category="InoIntHelper",
            description="Generates a random integer within a range, with optional zero-padded string output.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("int_min", default=0, min=0, max=999999),
                io.Int.Input("int_max", default=999999, min=0, max=999999),
                io.Int.Input("length", default=1, min=0, max=10),
            ],
            outputs=[
                io.Int.Output(display_name="random_int"),
                io.String.Output(display_name="formatted_int"),
            ],
        )

    @classmethod
    def execute(cls, enabled, int_min, int_max, length) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(-1, "")
        random_int = random.randint(int_min, int_max)
        formatted_int = str(random_int).zfill(length)
        return io.NodeOutput(random_int, formatted_int)


class InoIntToString(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoIntToString",
            display_name="Ino Int To String",
            category="InoIntHelper",
            description="Converts an integer to a string.",
            inputs=[
                io.Int.Input("input_int", default=0),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_int) -> io.NodeOutput:
        return io.NodeOutput(str(input_int))


class InoIntToFloat(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoIntToFloat",
            display_name="Ino Int To Float",
            category="InoIntHelper",
            description="Converts an integer to a float.",
            inputs=[
                io.Int.Input("input_int", default=0),
            ],
            outputs=[
                io.Float.Output(display_name="float"),
            ],
        )

    @classmethod
    def execute(cls, input_int) -> io.NodeOutput:
        return io.NodeOutput(float(input_int))


class InoCompareInt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoCompareInt",
            display_name="Ino Compare Int",
            category="InoIntHelper",
            description="Compares two integer values using a selected operator.",
            inputs=[
                io.Int.Input("int_a", default=0),
                io.Int.Input("int_b", default=0),
                io.Combo.Input("compare", options=["=", "<", ">", "<=", ">=", "<>"]),
            ],
            outputs=[
                io.Boolean.Output()
            ]
        )

    @classmethod
    def execute(cls, int_a, int_b, compare) -> io.NodeOutput:
        ops = {
            "=": int_a == int_b,
            "<": int_a < int_b,
            ">": int_a > int_b,
            "<=": int_a <= int_b,
            ">=": int_a >= int_b,
            "<>": int_a != int_b,
        }
        return io.NodeOutput(ops[compare])


class InoMathInt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoMathInt",
            display_name="Ino Math Int",
            category="InoIntHelper",
            description="Performs a math operation on two integers: add, subtract, multiply, divide, modulo, power.",
            inputs=[
                io.Int.Input("int_a", default=0),
                io.Int.Input("int_b", default=0),
                io.Combo.Input("operation", options=["add", "subtract", "multiply", "divide", "modulo", "power"]),
            ],
            outputs=[
                io.Int.Output(display_name="int"),
                io.Float.Output(display_name="float"),
            ],
        )

    @classmethod
    def execute(cls, int_a, int_b, operation) -> io.NodeOutput:
        if operation == "add":
            r = int_a + int_b
        elif operation == "subtract":
            r = int_a - int_b
        elif operation == "multiply":
            r = int_a * int_b
        elif operation == "divide":
            r = int_a / int_b if int_b != 0 else 0
        elif operation == "modulo":
            r = int_a % int_b if int_b != 0 else 0
        else:
            r = int_a ** int_b
        return io.NodeOutput(int(r), float(r))


LOCAL_NODE_CLASS = {
    "InoRandomIntInRange": InoRandomIntInRange,
    "InoIntToString": InoIntToString,
    "InoIntToFloat": InoIntToFloat,
    "InoCompareInt": InoCompareInt,
    "InoMathInt": InoMathInt,
}
LOCAL_NODE_NAME = {
    "InoRandomIntInRange": "Ino Random Int In Range",
    "InoIntToString": "Ino Int To String",
    "InoIntToFloat": "Ino Int To Float",
    "InoCompareInt": "Ino Compare Int",
    "InoMathInt": "Ino Math Int",
}
