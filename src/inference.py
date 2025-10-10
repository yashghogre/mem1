from llama_cpp import Llama

def inference():
    llm = Llama(
        model_path="models/gemma-3-270m.gguf",
        n_gpu_layers=-1,
        n_ctx=32768,
        verbose=False,
    )

    output = llm.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": "Who is the prime minister of India?",
            },
        ],
        temperature=1.0,
        stream=False,
    )

    return output["choices"][0]["message"]["content"]
