from llama_cpp import Llama

from config import CONFIG
from src.models import Message, LLMResponse

def inference(query: str):
    llm = Llama(
        model_path=CONFIG.MODEL_PATH,
        n_gpu_layers=-1,
        n_ctx=CONFIG.CTX_LENGTH,
        verbose=False,
    )

    system_msg = Message(
        role="system",
        content="You are a helpful assistant.",
    )

    user_msg = Message(
        role="user",
        content=query,
    )

    output = llm.create_chat_completion(
        messages=[
            system_msg.model_dump(),
            user_msg.model_dump(),
        ],
        temperature=CONFIG.MODEL_TEMP,
        stream=False,
    )

    response = LLMResponse.model_validate(output)
    return response.choices[0].message.content
