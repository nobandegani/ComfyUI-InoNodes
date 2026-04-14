import os

from inopyutils import InoJsonHelper, InoOpenAIHelper
from openai import OpenAI

from comfy_api.latest import io

from ..node_helper import ino_print_log, FailureInvalidatesCacheMixin


class InoOpenaiResponses(FailureInvalidatesCacheMixin, io.ComfyNode):
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
            cls._bump_failure()
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

            response = client.responses.create(model=model, input=response_input)

            error_message = response.error.message if response.error else "none"
            response_output = InoJsonHelper.dict_to_string(response.output)["data"] if response.output else "empty"
            response_text = response.output_text if response.output_text else "empty"

            return io.NodeOutput(True, response.id, response.status, error_message, response_text, response_output)
        except Exception as e:
            ino_print_log("InoOpenaiResponses", "", e)
            cls._bump_failure()
            return io.NodeOutput(False, "", "Openai response failed", str(e), "", "")


class InoOpenaiChatCompletions(FailureInvalidatesCacheMixin, io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoOpenaiChatCompletions",
            display_name="Ino Openai Chat Completions",
            category="InoOpenaiHelper",
            description="Sends a chat completion request to any OpenAI-compatible API with optional system prompt and image.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("user_prompt", default=""),
                io.String.Input("openai_api_key", default="", optional=True),
                io.String.Input("base_url", default="https://api.openai.com/v1", optional=True),
                io.String.Input("model", default="gpt-5", optional=True),
                io.String.Input("system_prompt", default="", optional=True),
                io.String.Input("image_url", default="", optional=True),
                io.Float.Input("temperature", default=0.7, min=0.0, max=2.0, step=0.1, optional=True),
                io.Int.Input("max_tokens", default=1024, min=1, max=128000, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="response"),
                io.String.Output(display_name="finish_reason"),
                io.String.Output(display_name="error"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, user_prompt, openai_api_key="", base_url="https://api.openai.com/v1",
                      model="gpt-5", system_prompt="", image_url="", temperature=0.7, max_tokens=1024) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoOpenaiChatCompletions", "Node is disabled")
            cls._bump_failure()
            return io.NodeOutput(False, "", "", "not enabled")

        try:
            api_key = openai_api_key if openai_api_key else os.getenv('OPENAI_TOKEN', '')
            base_url = base_url if base_url else os.getenv('OPENAI_URL', '')
            model = model if model else os.getenv('OPENAI_MODEL', '')
            image = image_url if image_url else None

            result = await InoOpenAIHelper.chat_completions(
                api_key=api_key, base_url=base_url, model=model,
                user_prompt=user_prompt, system_prompt=system_prompt,
                image=image, temperature=temperature, max_tokens=max_tokens,
            )

            if result.get("success"):
                return io.NodeOutput(True, result.get("response", ""), result.get("finish_reason", ""), "none")
            else:
                error_msg = result.get("message", "unknown error")
                ino_print_log("InoOpenaiChatCompletions", "", error_msg)
                cls._bump_failure()
                return io.NodeOutput(False, "", "", error_msg)
        except Exception as e:
            ino_print_log("InoOpenaiChatCompletions", "", e)
            cls._bump_failure()
            return io.NodeOutput(False, "", "", str(e))


LOCAL_NODE_CLASS = {
    "InoOpenaiResponses": InoOpenaiResponses,
    "InoOpenaiChatCompletions": InoOpenaiChatCompletions,
}
LOCAL_NODE_NAME = {
    "InoOpenaiResponses": "Ino Openai Responses",
    "InoOpenaiChatCompletions": "Ino Openai Chat Completions",
}
