from inopyutils import InoJsonHelper, InoHttpHelper

from comfy_api.latest import io

from ..node_helper import ino_print_log


class InoHttpCall(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="InoHttpCall",
            display_name="Ino Http Call",
            category="InoHttpHelper",
            description="Makes an HTTP request (GET/POST/PUT/DELETE/PATCH) and returns the response.",
            is_output_node=True,
            inputs=[
                io.Boolean.Input("enabled", default=True, label_off="OFF", label_on="ON"),
                io.String.Input("url", default="http://127.0.0.1:3313/health"),
                io.Combo.Input("request_type", options=["get", "post", "put", "delete", "patch"]),
                io.String.Input("headers", default='{"Connection": "keep-alive"}'),
                io.String.Input("json_payload", default=""),
                io.Boolean.Input("trust_env", default=False, optional=True),
                io.Boolean.Input("allow_redirects", default=False, optional=True),
                io.Int.Input("max_retries", default=10, min=1, max=50, optional=True),
            ],
            outputs=[
                io.Boolean.Output(display_name="success"),
                io.Int.Output(display_name="status_code"),
                io.String.Output(display_name="message"),
                io.String.Output(display_name="response"),
            ],
        )

    @classmethod
    async def execute(cls, enabled, url, request_type, headers, json_payload,
                      trust_env=False, allow_redirects=False, max_retries=10) -> io.NodeOutput:
        if not enabled:
            ino_print_log("InoHttpCall", "Attempt to run but disabled")
            return io.NodeOutput(False, 0, "Attempt to run but disabled", "")

        http_client = None
        try:
            http_client = InoHttpHelper(retries=max_retries, trust_env=trust_env)

            if InoJsonHelper.is_valid(headers):
                headers = InoJsonHelper.string_to_dict(headers)["data"]
            else:
                headers = {}

            if InoJsonHelper.is_valid(json_payload):
                json_payload = InoJsonHelper.string_to_dict(json_payload)["data"]
            else:
                json_payload = {}

            if request_type == "get":
                resp = await http_client.get(url=url, headers=headers, allow_redirects=allow_redirects)
            elif request_type == "post":
                resp = await http_client.post(url=url, headers=headers, json=json_payload, allow_redirects=allow_redirects)
            elif request_type == "put":
                resp = await http_client.put(url, headers=headers, json=json_payload, allow_redirects=allow_redirects)
            elif request_type == "delete":
                resp = await http_client.delete(url, headers=headers, allow_redirects=allow_redirects)
            elif request_type == "patch":
                resp = await http_client.patch(url, headers=headers, json=json_payload, allow_redirects=allow_redirects)
            else:
                await http_client.close()
                ino_print_log("InoHttpCall", "Invalid request type", request_type)
                return io.NodeOutput(False, 0, "Invalid request type", "")

            await http_client.close()
            if not resp["success"]:
                ino_print_log("InoHttpCall", resp["msg"], resp)
                return io.NodeOutput(False, 0, resp["msg"], str(resp))

            ino_print_log("InoHttpCall", "Success")
            return io.NodeOutput(True, resp["status_code"], resp["msg"], resp["data"])
        except Exception as e:
            if http_client:
                await http_client.close()
            ino_print_log("InoHttpCall", "", e)
            return io.NodeOutput(False, 0, str(e), "")


LOCAL_NODE_CLASS = {
    "InoHttpCall": InoHttpCall,
}
LOCAL_NODE_NAME = {
    "InoHttpCall": "Ino Http Call",
}
