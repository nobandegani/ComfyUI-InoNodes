import asyncio
import re
import hashlib
import base64
from pathlib import Path

from comfy_api.latest import io

from ..node_helper import PARENT_FOLDER_OPTIONS, resolve_comfy_path


def _write_text_sync(abs_path, text):
    Path(abs_path).parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(text)


class InoStringToggleCase(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringToggleCase",
            display_name="Ino String Toggle Case",
            category="InoStringHelper",
            description="Converts a string to upper or lower case.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("input_string", default="Test String", multiline=True),
                io.Boolean.Input("toggle_to", default=True, label_off="Lower", label_on="Upper"),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, enabled, input_string, toggle_to) -> io.NodeOutput:
        if not enabled:
            return io.NodeOutput(input_string)
        result = str(input_string).upper() if toggle_to else str(input_string).lower()
        return io.NodeOutput(result)


class InoStringReplacePlaceholder(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringReplacePlaceholder",
            display_name="Ino String Replace Placeholder",
            category="InoStringHelper",
            description="Replaces all {placeholder} tokens in a string with the replacement value.",
            inputs=[
                io.String.Input("input_string", default="Test {String}"),
                io.String.Input("replace_string", default="Replaced"),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_string, replace_string) -> io.NodeOutput:
        return io.NodeOutput(re.sub(r"\{[^}]*\}", replace_string, input_string))


class InoStringReplace(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringReplace",
            display_name="Ino String Replace",
            category="InoStringHelper",
            description="Replaces all occurrences of a substring with another.",
            inputs=[
                io.String.Input("input_string", default="Test string"),
                io.String.Input("replace_from", default="Test"),
                io.String.Input("replace_to", default="Example"),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_string, replace_from, replace_to) -> io.NodeOutput:
        return io.NodeOutput(input_string.replace(replace_from, replace_to))


class InoStringStripSimple(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringStripSimple",
            display_name="Ino String Strip Simple",
            category="InoStringHelper",
            description="Removes all specified characters from a string.",
            inputs=[
                io.String.Input("input_string", default="Test {String}"),
                io.String.Input("strip_string", default="'[]{}()-_+="),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_string, strip_string) -> io.NodeOutput:
        if input_string is None:
            return io.NodeOutput("")
        translation_table = str.maketrans("", "", strip_string)
        return io.NodeOutput(input_string.translate(translation_table))


class InoStringToAlphabeticString(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringToAlphabeticString",
            display_name="Ino String To Alphabetic String",
            category="InoStringHelper",
            description="Hashes a string and converts it to a fixed-length alphabetic-only string.",
            inputs=[
                io.String.Input("input_string", default="mjp043n85se4z"),
                io.Int.Input("length", default=8, min=1, max=64),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_string, length) -> io.NodeOutput:
        if input_string is None:
            return io.NodeOutput("")

        alphabet = "abcdefghijklmnopqrstuvwxyz"
        digest = hashlib.sha256(input_string.encode()).digest()
        b32 = base64.b32encode(digest).decode().lower().rstrip("=")

        result_chars = []
        for ch in b32:
            if 'a' <= ch <= 'z':
                idx = ord(ch) - ord('a')
            else:
                idx = (ord(ch) - ord('2')) % 26
            result_chars.append(alphabet[idx])
            if len(result_chars) == length:
                break

        return io.NodeOutput("".join(result_chars))


class InoSaveText(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoSaveText",
            display_name="Ino Save Text",
            category="InoStringHelper",
            description="Saves a text string to a file in the specified folder.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("text", default="", multiline=True),
                io.Combo.Input("parent_folder", options=PARENT_FOLDER_OPTIONS),
                io.String.Input("folder", default=""),
                io.String.Input("filename", default="output.txt"),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="rel_path"),
                io.String.Output(display_name="abs_path"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, text, parent_folder, folder, filename) -> io.NodeOutput:
        rel_path, abs_path = resolve_comfy_path(parent_folder, folder, filename)

        if not enabled:
            return io.NodeOutput(False, "not enabled", rel_path, abs_path)
        try:
            await asyncio.to_thread(_write_text_sync, abs_path, text)
            return io.NodeOutput(True, "saved", rel_path, abs_path)
        except Exception as e:
            return io.NodeOutput(False, str(e), rel_path, abs_path)


class InoStringConcat(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringConcat",
            display_name="Ino String Concat",
            category="InoStringHelper",
            description="Joins two strings with an optional separator.",
            inputs=[
                io.String.Input("string_a", default="", multiline=True),
                io.String.Input("string_b", default="", multiline=True),
                io.String.Input("separator", default=""),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, string_a, string_b, separator) -> io.NodeOutput:
        return io.NodeOutput(f"{string_a}{separator}{string_b}")


class InoStringContains(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringContains",
            display_name="Ino String Contains",
            category="InoStringHelper",
            description="Checks if a string contains a substring. Optionally case-insensitive.",
            inputs=[
                io.String.Input("input_string", default=""),
                io.String.Input("substring", default=""),
                io.Boolean.Input("case_sensitive", default=True, label_off="Ignore Case", label_on="Case Sensitive"),
            ],
            outputs=[
                io.Boolean.Output(display_name="contains"),
            ],
        )

    @classmethod
    def execute(cls, input_string, substring, case_sensitive) -> io.NodeOutput:
        if case_sensitive:
            return io.NodeOutput(substring in input_string)
        return io.NodeOutput(substring.lower() in input_string.lower())


class InoStringLength(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringLength",
            display_name="Ino String Length",
            category="InoStringHelper",
            description="Returns the character count of a string.",
            inputs=[
                io.String.Input("input_string", default=""),
            ],
            outputs=[
                io.Int.Output(display_name="length"),
            ],
        )

    @classmethod
    def execute(cls, input_string) -> io.NodeOutput:
        return io.NodeOutput(len(input_string) if input_string else 0)


class InoStringTrim(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringTrim",
            display_name="Ino String Trim",
            category="InoStringHelper",
            description="Strips leading and/or trailing whitespace from a string.",
            inputs=[
                io.String.Input("input_string", default="", multiline=True),
                io.Combo.Input("mode", options=["both", "left", "right"]),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_string, mode) -> io.NodeOutput:
        if mode == "left":
            return io.NodeOutput(input_string.lstrip())
        elif mode == "right":
            return io.NodeOutput(input_string.rstrip())
        return io.NodeOutput(input_string.strip())


class InoStringSplit(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringSplit",
            display_name="Ino String Split",
            category="InoStringHelper",
            description="Splits a string by a delimiter and returns the part at the given index.",
            inputs=[
                io.String.Input("input_string", default=""),
                io.String.Input("delimiter", default=","),
                io.Int.Input("index", default=0, min=0, max=999),
            ],
            outputs=[
                io.String.Output(display_name="part"),
                io.Int.Output(display_name="count"),
            ],
        )

    @classmethod
    def execute(cls, input_string, delimiter, index) -> io.NodeOutput:
        parts = input_string.split(delimiter)
        count = len(parts)
        if index < count:
            return io.NodeOutput(parts[index].strip(), count)
        return io.NodeOutput("", count)


class InoStringStartsEndsWith(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringStartsEndsWith",
            display_name="Ino String Starts/Ends With",
            category="InoStringHelper",
            description="Checks if a string starts or ends with a given substring.",
            inputs=[
                io.String.Input("input_string", default=""),
                io.String.Input("substring", default=""),
                io.Combo.Input("mode", options=["starts_with", "ends_with"]),
            ],
            outputs=[
                io.Boolean.Output(display_name="result"),
            ],
        )

    @classmethod
    def execute(cls, input_string, substring, mode) -> io.NodeOutput:
        if mode == "starts_with":
            return io.NodeOutput(input_string.startswith(substring))
        return io.NodeOutput(input_string.endswith(substring))


class InoStringSlice(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoStringSlice",
            display_name="Ino String Slice",
            category="InoStringHelper",
            description="Extracts a substring by start and end index.",
            inputs=[
                io.String.Input("input_string", default=""),
                io.Int.Input("start", default=0, min=0, max=99999),
                io.Int.Input("end", default=0, min=0, max=99999),
            ],
            outputs=[
                io.String.Output(display_name="string"),
            ],
        )

    @classmethod
    def execute(cls, input_string, start, end) -> io.NodeOutput:
        if end == 0:
            return io.NodeOutput(input_string[start:])
        return io.NodeOutput(input_string[start:end])


LOCAL_NODE_CLASS = {
    "InoStringToggleCase": InoStringToggleCase,
    "InoStringReplacePlaceholder": InoStringReplacePlaceholder,
    "InoStringReplace": InoStringReplace,
    "InoStringStripSimple": InoStringStripSimple,
    "InoStringToAlphabeticString": InoStringToAlphabeticString,
    "InoSaveText": InoSaveText,
    "InoStringConcat": InoStringConcat,
    "InoStringContains": InoStringContains,
    "InoStringLength": InoStringLength,
    "InoStringTrim": InoStringTrim,
    "InoStringSplit": InoStringSplit,
    "InoStringStartsEndsWith": InoStringStartsEndsWith,
    "InoStringSlice": InoStringSlice,
}
LOCAL_NODE_NAME = {
    "InoStringToggleCase": "Ino String Toggle Case",
    "InoStringReplacePlaceholder": "Ino String Replace Placeholder",
    "InoStringReplace": "Ino String Replace",
    "InoStringStripSimple": "Ino String Strip Simple",
    "InoStringToAlphabeticString": "Ino String To Alphabetic String",
    "InoSaveText": "Ino Save Text",
    "InoStringConcat": "Ino String Concat",
    "InoStringContains": "Ino String Contains",
    "InoStringLength": "Ino String Length",
    "InoStringTrim": "Ino String Trim",
    "InoStringSplit": "Ino String Split",
    "InoStringStartsEndsWith": "Ino String Starts/Ends With",
    "InoStringSlice": "Ino String Slice",
}
