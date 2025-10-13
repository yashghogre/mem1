import asyncio
from langfuse.openai import AsyncOpenAI
from llama_cpp import Llama
from typing import Dict, List, Protocol

from config import CONFIG
from src.database.schema import Message
from src.models import Message, LLMResponse


class InferenceException(Exception):
    ...


class BaseInference(Protocol):
    async def run(self, msgs: List[Dict]) -> str:
        ...


class LlamaCppInference(BaseInference):
    async def run(self, msgs: List[Dict]) -> str:
        try:
            llm = Llama(
                model_path=CONFIG.MODEL_PATH,
                n_gpu_layers=-1,
                n_ctx=CONFIG.CTX_LENGTH,
                verbose=False,
            )

            output = llm.create_chat_completion(
                messages=msgs,
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

    async def run(self, msgs: List[Dict]) -> str:
        try:
            response = await self.openai_client.chat.completion.create(
                model=CONFIG.MODEL_NAME,
                messages=msgs,
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


    async def create_completion(self, query: List[Message]) -> str:
        if self.client_instance is None:
            raise InferenceException(f"Inference instance was not initiated successfully.")

        msgs_to_send = [msg.model_dump() for msg in msgs]
        return self.client_instance.run(query)
