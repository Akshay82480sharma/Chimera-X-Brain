from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

@app.get("/v1/models")
def get_models():
    return {
        "data": [
            {"id": "lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf", "object": "model", "owned_by": "organization-owner"}
        ]
    }

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    stream: bool = False

@app.post("/v1/chat/completions")
def chat_completions(req: dict):
    model = req.get("model", "unknown")
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": f"Mock response from LM Studio for model {model}",
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21}
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=1234)
