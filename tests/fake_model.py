"""A local stand-in for a model behind an OpenAI-compatible API, for OpenCode tests.

Each request to /v1/chat/completions is recorded in `requests`. The first request
of a conversation (no tool result yet) answers with the scripted tool call; any
later request answers with the text "done". Answers are streamed (SSE), as
OpenCode asks for them.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeModel:
    def __init__(self):
        self.requests = []
        self.tool_call = None  # (tool name, arguments dict) for the next conversation
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.handler())
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()

    def handler(self):
        model = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):  # model list
                self.reply_json({"object": "list", "data": [{"id": "fake", "object": "model"}]})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                model.requests.append(body)
                messages = body.get("messages", [])
                answered = any(m.get("role") == "tool" for m in messages)
                tools = {t.get("function", {}).get("name") for t in body.get("tools", [])}
                if model.tool_call and not answered and model.tool_call[0] in tools:
                    name, arguments = model.tool_call
                    delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                             "function": {"name": name, "arguments": json.dumps(arguments)}}]}
                    finish = "tool_calls"
                else:
                    delta, finish = {"role": "assistant", "content": "done"}, "stop"
                if not body.get("stream"):
                    message = {k: v for k, v in delta.items()}
                    self.reply_json({"id": "x", "object": "chat.completion", "model": "fake",
                                     "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                                     "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for chunk in ({"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                              {"choices": [{"index": 0, "delta": {}, "finish_reason": finish}],
                               "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}):
                    chunk.update(id="x", object="chat.completion.chunk", model="fake")
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                self.wfile.write(b"data: [DONE]\n\n")

            def reply_json(self, data):
                raw = json.dumps(data).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        return Handler
