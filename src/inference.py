from llama_cpp import Llama

from config import CONFIG

def inference(query: str):
    llm = Llama(
        # model_path="models/gemma-3-270m.gguf",
        model_path=CONFIG.MODEL_PATH,
        n_gpu_layers=-1,
        n_ctx=CONFIG.CTX_LENGTH,
        verbose=False,
    )

    output = llm.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": query,
            },
        ],
        temperature=CONFIG.MODEL_TEMP,
        stream=False,
    )

    return output["choices"][0]["message"]["content"]
