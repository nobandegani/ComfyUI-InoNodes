import asyncio
import os

from inopyutils import InoJsonHelper, InoOpenAIHelper
from openai import OpenAI

from comfy_api.latest import io

from ..node_helper import ino_print_log


class InoOpenaiResponses(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoOpenaiResponses",
            display_name="Ino Openai Responses",
            category="InoOpenaiHelper",
            description="Sends a text or image prompt to OpenAI Responses API and returns the result.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.Combo.Input("response_type", options=["text", "image"]),
                io.String.Input("text", default=""),
                io.String.Input("image_url", default=""),
                io.String.Input("openai_api_key", default="", optional=True),
                io.Float.Input("timeout", default=300, optional=True),
                io.Int.Input("max_retries", default=3, optional=True),
                io.Combo.Input("model", options=["gpt-5", "gpt-4.1"], optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="id"),
                io.String.Output(display_name="status"),
                io.String.Output(display_name="error"),
                io.String.Output(display_name="output_text"),
                io.String.Output(display_name="output"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, seed, response_type, text, image_url,
                      openai_api_key="", timeout=300, max_retries=3, model="gpt-5") -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoOpenaiResponses", "Node is disabled")
            return io.NodeOutput(False, "", "not enabled", "", "", "")

        try:
            api_key = openai_api_key if openai_api_key else os.getenv('OPENAI_TOKEN', '')
            client = OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)

            response_input = text
            if response_type == "image":
                response_input = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": text},
                            {"type": "input_image", "image_url": image_url}
                        ]
                    }
                ]

            response = await asyncio.to_thread(client.responses.create, model=model, input=response_input)

            error_message = response.error.message if response.error else "none"
            response_output = InoJsonHelper.dict_to_string(response.output)["data"] if response.output else "empty"
            response_text = response.output_text if response.output_text else "empty"

            return io.NodeOutput(True, response.id, response.status, error_message, response_text, response_output)
        except Exception as e:
            ino_print_log("InoOpenaiResponses", "", e)
            return io.NodeOutput(False, "", "Openai response failed", str(e), "", "")


def _serialize_tool_calls(tool_calls) -> str:
    """Best-effort JSON serialization of OpenAI tool_calls (list of objects)."""
    if not tool_calls:
        return ""
    try:
        # OpenAI SDK objects expose model_dump(); fall back to dict() / str()
        serialized = []
        for tc in tool_calls:
            if hasattr(tc, "model_dump"):
                serialized.append(tc.model_dump())
            elif hasattr(tc, "dict"):
                serialized.append(tc.dict())
            else:
                serialized.append(str(tc))
        return InoJsonHelper.dict_to_string(serialized)["data"]
    except Exception:
        return str(tool_calls)


class InoOpenaiChatCompletions(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoOpenaiChatCompletions",
            display_name="Ino Openai Chat Completions",
            category="InoOpenaiHelper",
            description="Sends a chat completion request to any OpenAI-compatible API (OpenAI, vLLM, RunPod, Modal) with optional system prompt and image.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                #io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
                io.String.Input("user_prompt", default=""),
                io.String.Input("openai_api_key", default="", optional=True),
                io.String.Input("base_url", default="https://api.openai.com/v1", optional=True),
                io.String.Input("model", default="gpt-5", optional=True),
                io.String.Input("system_prompt", default="", optional=True),
                io.String.Input("image_url", default="", optional=True),
                io.Float.Input("temperature", default=0.7, min=0.0, max=2.0, step=0.1, optional=True),
                io.Int.Input("max_tokens", default=1024, min=1, max=128000, optional=True),
                io.Float.Input("top_p", default=1.0, min=0.0, max=1.0, step=0.05, optional=True),
                io.Boolean.Input("enable_thinking", default=True, label_off="OFF", label_on="ON", optional=True, tooltip="Qwen3-style thinking phase toggle for vLLM. Ignored by OpenAI-only servers."),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="response"),
                io.String.Output(display_name="finish_reason"),
                io.String.Output(display_name="error"),
                io.String.Output(display_name="reasoning"),
                io.String.Output(display_name="tool_calls"),
                io.Int.Output(display_name="prompt_tokens"),
                io.Int.Output(display_name="completion_tokens"),
                io.Int.Output(display_name="total_tokens"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, user_prompt, openai_api_key="", base_url="https://api.openai.com/v1",
                      model="gpt-5", system_prompt="", image_url="", temperature=0.7, max_tokens=1024,
                      top_p=1.0, enable_thinking=True) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoOpenaiChatCompletions", "Node is disabled")
            return io.NodeOutput(False, "", "", "not enabled", "", "", 0, 0, 0)

        try:
            api_key = openai_api_key if openai_api_key else os.getenv('OPENAI_TOKEN', '')
            base_url = base_url if base_url else os.getenv('OPENAI_URL', '')
            model = model if model else os.getenv('OPENAI_MODEL', '')
            image = image_url if image_url else None

            result = await InoOpenAIHelper.chat_completions(
                api_key=api_key, base_url=base_url, model=model,
                user_prompt=user_prompt, system_prompt=system_prompt,
                image=image, temperature=temperature, max_tokens=max_tokens,
                top_p=top_p, enable_thinking=enable_thinking,
            )

            if result.get("success"):
                usage = result.get("usage") or {}
                reasoning = result.get("reasoning") or ""
                tool_calls_str = _serialize_tool_calls(result.get("tool_calls"))
                return io.NodeOutput(
                    True,
                    result.get("response", ""),
                    result.get("finish_reason") or "",
                    "none",
                    reasoning,
                    tool_calls_str,
                    int(usage.get("prompt_tokens") or 0),
                    int(usage.get("completion_tokens") or 0),
                    int(usage.get("total_tokens") or 0),
                )
            else:
                # ino_err uses the key "msg", not "message"
                error_msg = result.get("msg", "unknown error")
                ino_print_log("InoOpenaiChatCompletions", "", error_msg)
                return io.NodeOutput(False, "", "", error_msg, "", "", 0, 0, 0)
        except Exception as e:
            ino_print_log("InoOpenaiChatCompletions", "", e)
            return io.NodeOutput(False, "", "", str(e), "", "", 0, 0, 0)


LOCAL_NODE_CLASS = {
    "InoOpenaiResponses": InoOpenaiResponses,
    "InoOpenaiChatCompletions": InoOpenaiChatCompletions,
}
LOCAL_NODE_NAME = {
    "InoOpenaiResponses": "Ino Openai Responses",
    "InoOpenaiChatCompletions": "Ino Openai Chat Completions",
}
