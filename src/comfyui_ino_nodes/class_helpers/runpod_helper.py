import os

from inopyutils import InoRunpodHelper, ino_is_err

from comfy_api.latest import io

from ..node_helper import ino_print_log, FailureInvalidatesCacheMixin


class InoVllmRunSync(FailureInvalidatesCacheMixin, io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoVllmRunSync",
            display_name="Ino Vllm Run Sync",
            category="InoRunpodHelper",
            description="Runs a synchronous vLLM inference request on Runpod serverless with optional image input.",
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("url", default=""),
                io.String.Input("api_key", default=""),
                io.String.Input("model", default=""),
                io.String.Input("user_prompt", default=""),
                io.String.Input("system_prompt", default="", optional=True),
                io.String.Input("image_url", default="", optional=True),
                io.Float.Input("temperature", default=0.7, min=0.0, max=2.0, step=0.1, optional=True),
                io.Int.Input("max_tokens", default=1024, min=1, max=128000, optional=True),
                io.Float.Input("timeout", default=300.0, min=10.0, max=600.0, step=10.0, optional=True),
                io.Int.Input("max_polls", default=24, min=1, max=100, optional=True),
                io.Float.Input("poll_delay", default=10.0, min=1.0, max=60.0, step=1.0, optional=True),
                io.Int.Input("max_failed_retries", default=5, min=0, max=20, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.String.Output(display_name="id"),
                io.String.Output(display_name="status"),
                io.Int.Output(display_name="delay_time"),
                io.Int.Output(display_name="execution_time"),
                io.String.Output(display_name="response"),
                io.String.Output(display_name="reasoning"),
                io.String.Output(display_name="finish_reason"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, url, api_key, model, user_prompt,
                      system_prompt="", image_url="", temperature=0.7, max_tokens=1024,
                      timeout=300.0, max_polls=24, poll_delay=10.0, max_failed_retries=5) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoVllmRunSync", "Node is disabled")
            cls._bump_failure()
            return io.NodeOutput(False, "", "not enabled", 0, 0, "", "", "")

        try:
            api_key = api_key if api_key else os.getenv('RUNPOD_LLM_API', '')
            url = url if url else os.getenv('RUNPOD_LLM_URL', '')
            model = model if model else os.getenv('RUNPOD_LLM_MODEL', '')

            image = image_url if image_url else None

            response = await InoRunpodHelper.serverless_vllm_runsync(
                url=url, api_key=api_key, model=model,
                user_prompt=user_prompt, system_prompt=system_prompt,
                image=image, temperature=temperature, max_tokens=max_tokens,
                timeout=timeout, max_polls=max_polls, poll_delay=poll_delay,
                max_failed_retries=max_failed_retries,
            )

            if ino_is_err(response):
                cls._bump_failure()
                return io.NodeOutput(False, "", response.get("msg", "unknown error"), 0, 0, "", "", "")

            return io.NodeOutput(
                True,
                response.get("id", ""),
                response.get("status", ""),
                response.get("delay_time", 0),
                response.get("execution_time", 0),
                response.get("response", ""),
                response.get("reasoning", ""),
                response.get("finish_reason", ""),
            )
        except Exception as e:
            ino_print_log("InoVllmRunSync", "", e)
            cls._bump_failure()
            return io.NodeOutput(False, "", f"response failed: {e}", 0, 0, "", "", "")


LOCAL_NODE_CLASS = {
    "InoVllmRunSync": InoVllmRunSync,
}
LOCAL_NODE_NAME = {
    "InoVllmRunSync": "Ino Vllm Run Sync",
}
