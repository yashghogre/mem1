import asyncio
from langfuse.openai import AsyncOpenAI
from llama_cpp import Llama
from typing import Protocol

from config import CONFIG
from src.models import Message, LLMResponse


class InferenceException(Exception):
    ...


#TODO: change query from `str` to stream of messages (List of messages).

class BaseInference(Protocol):
    async def run(self, query: str) -> str | InferenceException:
        ...


class LlamaCppInference(BaseInference):
    async def run(self, query: str) -> str | InferenceException:
        try:
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
        
        except Exception as e:
            raise InferenceException(f"Llama-cpp inference failed. Error: {str(e)}")


class OpenAIInference(BaseInference):
    def __init__(self):
        self.openai_client = OpenAI(
            base_url=CONFIG.MODEL_BASE_URL,
            api_key=CONFIG.MODEL_API_KEY,            
        )

    async def run(self, query: str) -> str | InferenceException:
        try:
            system_msg = Message(
                role="system",
                content="You are a helpful assistant.",
            )

            user_msg = Message(
                role="user",
                content=query,
            )

            response = await self.openai_client.chat.completion.create(
                model=CONFIG.MODEL_NAME,
                messages=[
                    system_msg.model_dump(),
                    user_msg.model_dump(),
                ],
                temperature=CONFIG.MODEL_TEMP,
            )
            return response.choices[0].message.content
        
        except Exception as e:
            raise InferenceException(f"OpenAI inference failed. Error: {str(e)}")


class Inference:
    def __init__(self):
        self.client_instance = None
        self.inference_type = CONFIG.INFERENCE_TYPE
        match self.inference_type:
            case "local":
                self.client_instance = LlamaCppInference()
            case "api":
                self.client_instance = OpenAIInference()
            case _:
                raise InferenceException(f"Invalid inference option provided. Please provide a valid inference option between `local` and `api`")


    async def create_completion(self, query: str) -> str | InferenceException:
        try:
            if self.client_instance is None:
                raise InferenceException(f"Inference instance was not initiated successfully.")
            return self.client_instance.run(query)
