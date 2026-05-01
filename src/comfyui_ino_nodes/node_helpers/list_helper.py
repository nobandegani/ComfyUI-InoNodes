"""List-construction and list-manipulation nodes.

All list-consuming nodes use schema-level `is_input_list=True` so the upstream
list reaches `execute` as a single Python list, instead of being expanded into
multiple invocations. With that flag, ComfyUI also wraps every scalar input in
a 1-element list, so we unwrap scalars below before using them.
"""
from comfy_api.latest import io


def _unwrap_scalar(v):
    """Unwrap a 1-element list back to its scalar (for is_input_list inputs)."""
    if isinstance(v, list) and len(v) == 1:
        return v[0]
    return v


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------

class InoMakeAnyList(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoMakeAnyList",
            display_name="Ino Make Any List",
            category="InoListHelper",
            description="Collects up to 10 inputs of any type into a single list. Optionally drops slots that are None (unwired).",
            inputs=[
                io.AnyType.Input("any_1", optional=True),
                io.AnyType.Input("any_2", optional=True),
                io.AnyType.Input("any_3", optional=True),
                io.AnyType.Input("any_4", optional=True),
                io.AnyType.Input("any_5", optional=True),
                io.AnyType.Input("any_6", optional=True),
                io.AnyType.Input("any_7", optional=True),
                io.AnyType.Input("any_8", optional=True),
                io.AnyType.Input("any_9", optional=True),
                io.AnyType.Input("any_10", optional=True),
                io.Boolean.Input("skip_none", default=True, optional=True, label_off="keep all", label_on="skip None", tooltip="When ON, slots that are None (typically unwired inputs) are excluded. Other falsy values (0, False, '', []) are always kept."),
            ],
            outputs=[
                io.AnyType.Output(display_name="list", is_output_list=True),
                io.Int.Output(display_name="count"),
            ],
        )

    @classmethod
    def execute(
        cls,
        any_1=None, any_2=None, any_3=None, any_4=None, any_5=None,
        any_6=None, any_7=None, any_8=None, any_9=None, any_10=None,
        skip_none=True,
    ) -> io.NodeOutput:
        items = [
            any_1, any_2, any_3, any_4, any_5,
            any_6, any_7, any_8, any_9, any_10,
        ]
        if skip_none:
            items = [v for v in items if v is not None]
        return io.NodeOutput(items, len(items))


# ---------------------------------------------------------------------------
# Inspectors / accessors (consume a list)
# ---------------------------------------------------------------------------

class InoListLength(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoListLength",
            display_name="Ino List Length",
            category="InoListHelper",
            description="Returns the number of items in a list.",
            is_input_list=True,
            inputs=[
                io.AnyType.Input("items"),
            ],
            outputs=[
                io.Int.Output(display_name="length"),
            ],
        )

    @classmethod
    def execute(cls, items) -> io.NodeOutput:
        if items is None:
            return io.NodeOutput(0)
        return io.NodeOutput(len(items))


class InoListGetItem(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoListGetItem",
            display_name="Ino List Get Item",
            category="InoListHelper",
            description="Gets the item at the specified index. Negative indices count from the end. `success` is False if the list is empty or the index is out of range.",
            is_input_list=True,
            inputs=[
                io.AnyType.Input("items"),
                io.Int.Input("index", default=0, min=-99999, max=99999),
            ],
            outputs=[
                io.AnyType.Output(display_name="item"),
                io.Boolean.Output(display_name="success"),
                io.Int.Output(display_name="length"),
            ],
        )

    @classmethod
    def execute(cls, items, index) -> io.NodeOutput:
        index = _unwrap_scalar(index)
        if not items:
            return io.NodeOutput(None, False, 0)
        n = len(items)
        if index < -n or index >= n:
            return io.NodeOutput(None, False, n)
        return io.NodeOutput(items[index], True, n)


class InoListGetFirst(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoListGetFirst",
            display_name="Ino List Get First",
            category="InoListHelper",
            description="Returns the first item in a list. `success` is False if the list is empty.",
            is_input_list=True,
            inputs=[
                io.AnyType.Input("items"),
            ],
            outputs=[
                io.AnyType.Output(display_name="item"),
                io.Boolean.Output(display_name="success"),
                io.Int.Output(display_name="length"),
            ],
        )

    @classmethod
    def execute(cls, items) -> io.NodeOutput:
        if not items:
            return io.NodeOutput(None, False, 0)
        return io.NodeOutput(items[0], True, len(items))


class InoListGetLast(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoListGetLast",
            display_name="Ino List Get Last",
            category="InoListHelper",
            description="Returns the last item in a list. `success` is False if the list is empty.",
            is_input_list=True,
            inputs=[
                io.AnyType.Input("items"),
            ],
            outputs=[
                io.AnyType.Output(display_name="item"),
                io.Boolean.Output(display_name="success"),
                io.Int.Output(display_name="length"),
            ],
        )

    @classmethod
    def execute(cls, items) -> io.NodeOutput:
        if not items:
            return io.NodeOutput(None, False, 0)
        return io.NodeOutput(items[-1], True, len(items))


# ---------------------------------------------------------------------------
# Mutations (return a new list)
# ---------------------------------------------------------------------------

class InoListAppend(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoListAppend",
            display_name="Ino List Append",
            category="InoListHelper",
            description=(
                "Appends one or more items to a list and returns the combined list. "
                "If `item` is wired from a list-output node, all of its items are appended (extend behavior). "
                "If wired from a regular node, the single value is appended."
            ),
            is_input_list=True,
            inputs=[
                io.AnyType.Input("items"),
                io.AnyType.Input("item"),
            ],
            outputs=[
                io.AnyType.Output(display_name="list", is_output_list=True),
                io.Int.Output(display_name="count"),
            ],
        )

    @classmethod
    def execute(cls, items, item) -> io.NodeOutput:
        # With is_input_list=True, both arrive as lists. A scalar from a
        # regular upstream comes as a 1-element list — concatenating either
        # way is correct for both append-one and extend-many.
        base = list(items) if items else []
        addition = list(item) if item else []
        result = base + addition
        return io.NodeOutput(result, len(result))


LOCAL_NODE_CLASS = {
    "InoMakeAnyList": InoMakeAnyList,
    "InoListLength": InoListLength,
    "InoListGetItem": InoListGetItem,
    "InoListGetFirst": InoListGetFirst,
    "InoListGetLast": InoListGetLast,
    "InoListAppend": InoListAppend,
}
LOCAL_NODE_NAME = {
    "InoMakeAnyList": "Ino Make Any List",
    "InoListLength": "Ino List Length",
    "InoListGetItem": "Ino List Get Item",
    "InoListGetFirst": "Ino List Get First",
    "InoListGetLast": "Ino List Get Last",
    "InoListAppend": "Ino List Append",
}
