import asyncio

from comfy_api.latest import io

from ..node_helper import ino_print_log, log_capture

class InoRelay(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        execute_template = io.MatchType.Template("execute")
        relay_template = io.MatchType.Template("relay")
        return io.Schema(
            node_id="InoRelay",
            display_name="Ino Relay",
            category="InoExtraNodes",
            description="Passes through two values of any type. Useful for controlling execution order.",
            inputs=[
                io.MatchType.Input("execute", template=execute_template),
                io.MatchType.Input("relay", template=relay_template),
            ],
            outputs=[
                io.MatchType.Output(template=execute_template, display_name="execute"),
                io.MatchType.Output(template=relay_template, display_name="relay"),
            ],
        )

    @classmethod
    def execute(cls, execute, relay) -> io.NodeOutput:
        return io.NodeOutput(execute, relay)

class InoAnyEqual(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.MatchType.Template("compare")
        return io.Schema(
            node_id="InoAnyEqual",
            display_name="Ino Any Equal",
            category="InoExtraNodes",
            description="Compares two values of the same type for equality.",
            inputs=[
                io.MatchType.Input("input", template=template),
                io.MatchType.Input("compare", template=template),
            ],
            outputs=[
                io.Boolean.Output(display_name="equal"),
            ],
        )

    @classmethod
    def execute(cls, input, compare) -> io.NodeOutput:
        return io.NodeOutput(input == compare)


class InoDelayAsync(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.MatchType.Template("relay")
        return io.Schema(
            node_id="InoDelayAsync",
            display_name="Ino Delay Async",
            category="InoExtraNodes",
            description="Delays execution for a specified number of seconds before passing through the value.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.MatchType.Input("relay", template=template),
                io.Float.Input("delay", default=0.0, min=0.0, max=10000.0, step=0.1),
            ],
            outputs=[
                io.MatchType.Output(template=template, display_name="output"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, relay, delay) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(relay)

        await asyncio.sleep(delay)
        return io.NodeOutput(relay)

class InoPrintLog(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.MatchType.Template("relay")
        return io.Schema(
            node_id="InoPrintLog",
            display_name="Ino Print Log",
            category="InoExtraNodes",
            description="Prints a log message to the console and passes through the relay value.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.MatchType.Input("relay", template=template),
                io.String.Input("log_message", default="Log message", multiline=True),
            ],
            outputs=[
                io.MatchType.Output(template=template, display_name="output"),
            ],
        )

    @classmethod
    def execute(cls, enabled, relay, log_message) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(relay)

        ino_print_log("", log_message)
        return io.NodeOutput(relay)

class InoRandomNoise(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoRandomNoise",
            display_name="Ino Random Noise",
            category="InoSamplerHelper",
            description="Generates random noise with selectable 32-bit or 64-bit seed precision.",
            inputs=[
                io.Int.Input("noise_seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.Boolean.Input("precision", default=True, label_off="32-bit", label_on="64-bit"),
            ],
            outputs=[
                io.Noise.Output(display_name="noise"),
                io.Int.Output(display_name="seed"),
            ],
        )

    @classmethod
    def execute(cls, noise_seed, precision) -> io.NodeOutput:
        from comfy_extras.nodes_custom_sampler import Noise_RandomNoise

        if precision:
            final_seed = noise_seed & 0xFFFFFFFFFFFFFFFF
        else:
            final_seed = noise_seed & 0xFFFFFFFF

        random_seed = Noise_RandomNoise(final_seed)
        return io.NodeOutput(random_seed, final_seed)

class InoSwitchOnBool(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.MatchType.Template("switch")
        return io.Schema(
            node_id="InoSwitchOnBool",
            display_name="Ino Switch On Bool",
            category="InoExtraNodes",
            description="Routes one of two inputs based on a boolean switch. Uses lazy evaluation.",
            is_experimental=True,
            inputs=[
                io.Boolean.Input("switch"),
                io.MatchType.Input("on_false", template=template, lazy=True),
                io.MatchType.Input("on_true", template=template, lazy=True),
            ],
            outputs=[
                io.MatchType.Output(template=template, display_name="output"),
            ],
        )

    @classmethod
    def check_lazy_status(cls, switch, on_false=None, on_true=None):
        if switch and on_true is None:
            return ["on_true"]
        if not switch and on_false is None:
            return ["on_false"]

    @classmethod
    def execute(cls, switch, on_true, on_false) -> io.NodeOutput:
        return io.NodeOutput(on_true if switch else on_false)

MISSING = object()

class InoSwitchOnInt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.MatchType.Template("switch")
        return io.Schema(
            node_id="InoSwitchOnInt",
            display_name="Ino Switch On Int",
            category="InoExtraNodes",
            description="Routes one of up to 10 inputs based on an integer index. Falls back to default if the selected input is not connected.",
            is_experimental=True,
            inputs=[
                io.Int.Input("switch", default=0, min=0),
                io.MatchType.Input("default", template=template, lazy=True),
                *[io.MatchType.Input(f"input_{i}", template=template, optional=True, lazy=True) for i in range(0, 10)],
            ],
            outputs=[
                io.MatchType.Output(template=template, display_name="output"),
            ],
        )

    @classmethod
    def check_lazy_status(cls, switch, default=MISSING, **kwargs):
        needed = []
        key = f"input_{switch}"
        selected = kwargs.get(key, MISSING)
        if selected is None:
            needed.append(key)
        elif selected is MISSING:
            if default is None:
                needed.append("default")
        return needed if needed else None

    @classmethod
    def execute(cls, switch, default=MISSING, **kwargs) -> io.NodeOutput:
        result = kwargs.get(f"input_{switch}", MISSING)
        if result is not MISSING:
            return io.NodeOutput(result)
        fallback = default if default is not MISSING else None
        return io.NodeOutput(fallback)

class InoLength(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        template = io.MatchType.Template("input")
        return io.Schema(
            node_id="InoLength",
            display_name="Ino Length",
            category="InoExtraNodes",
            description="Returns the length of a list or tuple input.",
            is_input_list=True,
            inputs=[
                io.MatchType.Input("input", template=template),
            ],
            outputs=[
                io.Int.Output(display_name="length"),
            ],
        )

    @classmethod
    def execute(cls, input) -> io.NodeOutput:
        if not isinstance(input, (list, tuple)):
            return io.NodeOutput(-1)
        return io.NodeOutput(len(input))

class InoTerminalLog(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoTerminalLog",
            display_name="Ino Terminal Log",
            category="InoExtraNodes",
            description="Captures and returns the last N lines from the terminal stdout.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("lines", default=50, min=1, max=10000),
            ],
            outputs=[
                io.String.Output(display_name="log"),
            ],
        )

    @classmethod
    def execute(cls, enabled, lines) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput("")
        captured = log_capture.get_lines(lines)
        return io.NodeOutput("\n".join(captured))


LOCAL_NODE_CLASS = {
    "InoRelay": InoRelay,
    "InoAnyEqual": InoAnyEqual,
    "InoDelayAsync": InoDelayAsync,
    "InoPrintLog": InoPrintLog,
    "InoRandomNoise": InoRandomNoise,
    "InoSwitchOnBool": InoSwitchOnBool,
    "InoSwitchOnInt": InoSwitchOnInt,
    "InoLength": InoLength,
    "InoTerminalLog": InoTerminalLog,
}
LOCAL_NODE_NAME = {
    "InoRelay": "Ino Relay",
    "InoAnyEqual": "Ino Any Equal",
    "InoDelayAsync": "Ino Delay Async",
    "InoPrintLog": "Ino Print Log",
    "InoRandomNoise": "Ino Random Noise",
    "InoSwitchOnBool": "Ino Switch On Bool",
    "InoSwitchOnInt": "Ino Switch On Int",
    "InoLength": "Ino Length",
    "InoTerminalLog": "Ino Terminal Log",
}
