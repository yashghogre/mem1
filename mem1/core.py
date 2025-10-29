import asyncio
from beanie import Document
from copy import deepcopy
import httpx
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from textwrap import dedent
from typing import List, Optional

from infra.database.schema import Message
#TODO: Completely remove the MongoDB dependency for summary
# of figure out a way to include this schema in the
# already intialized MongoDB client.

from .infra.database import DatabaseUtils
from .infra.embedder import EmbedderUtils
# from .infra.schema import Message
from .infra.vectordb import VectorDBUtils
from .utils.enums import FactComparisonResult
from .utils.models import FactsComparisonResultModel
from .utils.prompts import (
    SUMMARY_PROMPT,
    CANDIDATE_FACT_PROMPT,
    COMPARE_OLD_AND_NEW_FACT_PROMPT,
)


logger = logging.getLogger(__name__)


class Mem1Exception(Exception):
    def __init__(
        self,
        error: str,
        message: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.error = error
        self.message = message
        self.suggestion = suggestion

    def __repr__(self):
        return dedent(f"""
        Error in Mem1 Client.
        {self.message}
        Error: {self.error}.
        Suggestion: {self.suggestion or " "}
        """)


class Mem1:
    def __init__(
        self,
        chat_client: AsyncOpenAI,
        model_name: str,
        vector_db_client: AsyncQdrantClient,
        vector_db_collection: str,
        embedder_client: httpx.AsyncClient,
        database_client: AsyncIOMotorClient,    #NOTE: Will remove this once I figure out a more efficient way to store the summary.
        database_collection: Document,
        max_memories_in_vector_db: Optional[int] = 10,
        message_interval_for_summary: Optional[int] = 5,
        max_messages_for_new_fact: Optional[int] = 10,
    ):
        self.chat_client = chat_client
        self.model_name = model_name
        self.database_client = database_client
        self.database_collection = database_collection
        self.embedder_client = embedder_client
        self.vector_db_client = vector_db_client
        self.vector_db_collection = vector_db_collection

        self.max_memories_in_vector_db = max_memories_in_vector_db
        self.message_interval_for_summary = message_interval_for_summary
        self.max_messages_for_new_fact = max_messages_for_new_fact

        self.db_utils = DatabaseUtils(
            db_client=self.database_client,
            collection=self.database_collection,
        )
        self.embedder = EmbedderUtils(embedder_client=self.embedder_client)
        self.vectordb_utils = VectorDBUtils(
            vectordb_client=self.vector_db_client,
            vectordb_collection=self.vector_db_collection,
            embedder=self.embedder,
        )


    async def _summarize_messages(self, messages: List[Message], prev_summary: Optional[str] = None) -> str:
        try:
            logger.info(f"Summarize messages called!")
            msgs = deepcopy(messages)
            msgs = msgs[-(self.max_messages_for_new_fact):]
            if prev_summary is None:
                prev_summary = "No Previous Summary Available."
            summary_prompt = SUMMARY_PROMPT.format(PREVIOUS_SUMMARY=prev_summary)
            sys_msg = Message(
                role="system",
                content=summary_prompt,
            )
            msgs.insert(0, sys_msg)
            logger.debug(f"messages for summary: {msgs}")

            response = await self.chat_client.chat.completions.create(
                model=self.model_name,
                messages=msgs,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Mem1Exception(message="Error while summarizing messages.", error=str(e))


    def _count_user_messages(self, messages: List[Message]) -> int:
        usr_msg_count = 0
        for msg in messages:
            if msg.role == "user":
                usr_msg_count += 1

        return usr_msg_count


    def _form_user_msg_for_candidate_fact(self, messages: List[Message], summary: str):
        user_msg = []
        user_msg.append(f"CONTEXTUAL SUMMARY:\n{summary}\n")
        user_msg.append(f"\nRECENT MESSAGES:\n")
        for msg in messages:
            user_msg.append(f"{msg.role} - {msg.content}")
        final_user_msg = Message(
            role="user",
            content="\n".join(user_msg),
        )
        return final_user_msg


    async def _find_candidate_fact(self, messages: List[Message], summary: str) -> str:
        try:
            if messages[-1].role != "user":
                raise Mem1Exception(
                    message="Error in the ordering of messages.",
                    error="The last message does not have the role `user`",
                    suggestion="Make sure the last message has the role `user`",
                )
            msgs = messages[-(self.max_messages_for_new_fact):]
            sys_msg = Message(
                role="system",
                content=CANDIDATE_FACT_PROMPT,
            )
            query_msg = self._form_user_msg_for_candidate_fact(msgs, summary)
            msgs_to_send = [sys_msg, query_msg]

            response = await self.chat_client.chat.completions.create(
                model=self.model_name,
                messages=msgs_to_send,
            )
            candidate_fact = response.choices[0].message.content
            logger.info(f"candidate fact: {candidate_fact}")
            return candidate_fact

        except Exception as e:
            raise Mem1Exception(
                message="Error while finding candidate fact.",
                error=str(e),
            )
            

    async def _compare_facts(self, old_fact: str, new_fact: str):
        try:
            sys_msg = Message(
                role="system",
                content=COMPARE_OLD_AND_NEW_FACT_PROMPT,
            )
            usr_msg_content = f"OLD FACT:\n{old_fact}\n\nNEW CANDIDATE FACT:\n{new_fact}"
            logger.debug(f"msg for comparing facts: {usr_msg_content}")
            user_msg = Message(
                role="user",
                content=usr_msg_content,
            )
            msgs = [sys_msg, user_msg]
            response = await self.chat_client.beta.chat.completions.parse(
                model=self.model_name,
                messages=msgs,
                response_format=FactsComparisonResultModel,
            )
            res = response.choices[0].message.parsed
            logging.debug(f"facts comparison results: {res}")
            return res

        except Exception as e:
            raise Mem1Exception(
                message="Error while comparing facts.",
                error=str(e),
            )


    async def _add_fact(self, fact: str):
        try:
            all_facts = await self.vectordb_utils.retrieve_all_points()
            if all_facts is not None:
                if len(all_facts) > self.max_memories_in_vector_db:
                    await self.vectordb_utils.find_oldest_fact_and_delete()

            await self.vectordb_utils.store_point(fact)

        except Exception as e:
            raise Mem1Exception(
                message="Error while adding a new fact.",
                error=str(e),
            )


    async def _update_fact(self, new_fact: str, old_fact):
        try:
            await self.vectordb_utils.delete_point(old_fact)
            await self.vectordb_utils.store_point(new_fact)

        except Exception as e:
            raise Mem1Exception(
                message="Error while updating old fact.",
                error=str(e),
            )
        

    async def process_memory(self, messages: List[Message]):
        try:
            user_msg_count = self._count_user_messages(messages)
            prev_chat_summary = await self.db_utils.get_chat_summary()
            if prev_chat_summary is None:
                prev_chat_summary = "No previous chat summary available, make a new summary."
            else:
                prev_chat_summary = prev_chat_summary.summary

            if (user_msg_count - 1) % self.message_interval_for_summary == 0 or prev_chat_summary is None:
                chat_summary = await self._summarize_messages(messages=messages, prev_summary=prev_chat_summary)
                await self.db_utils.store_chat_summary(summary=chat_summary)
            else:
                chat_summary = prev_chat_summary

            candidate_fact = await self._find_candidate_fact(messages, chat_summary)
            old_fact_point = await self.vectordb_utils.retrieve_point(text=candidate_fact) or "No previous facts"
            if not isinstance(old_fact_point, str):
                logger.debug(f"old_fact_point: {old_fact_point}")
                old_fact = old_fact_point.payload.get("text")
            else:
                old_fact = "No previous facts"

            fact_comp_res = await self._compare_facts(old_fact, candidate_fact)
            comparison_res = fact_comp_res.result.strip()
            comparison_fact = fact_comp_res.fact.strip()

            match comparison_res:
                case FactComparisonResult.ADD.value:
                    logger.info("ADDING NEW FACT")
                    await self._add_fact(comparison_fact)

                case FactComparisonResult.UPDATE.value:
                    logger.info("UPDATING EXISTING FACT")
                    await self._update_fact(comparison_fact, old_fact_point)

                case FactComparisonResult.NONE.value:
                    logger.info("NO CHANGES TO FACTS")
                    pass

                case _:
                    raise Mem1Exception(
                        message="Error in LLM output while checking comparison results",
                        error=f"The LLM returned {fact_comp_res.strip()} which does not match any of `ADD`, `UPDATE` or `NONE`.",
                        suggestion="This is a LLM side error. Alter prompt for better results.",
                    )

            
        except Exception as e:
            raise Mem1Exception(
                message="Error while processing memory.",
                error=str(e)
            )


    async def load_memory(self, messages: List[Message]) -> List[Message]:
        try:
            msgs_copy = deepcopy(messages)
            sys_msg = msgs_copy[0]
            if sys_msg.role != "system":
                logger.error("Error while checking system message while loading memory. System message not found in the context.")
                raise Mem1Exception(
                    message="Error while checking system message.",
                    error="System message not found in the context.",
                    suggestion="Make sure to include system message in the context.",
                )

            user_memories = await self.vectordb_utils.retrieve_all_points()
            if user_memories is None:
                return msgs_copy

            memories_arr = [mem.payload.get("text") for mem in user_memories]
            memories_arr.insert(0, "\nHere are some long-term memories of the user:")
            memories_str = "\n".join(memories_arr)

            msgs_copy[0].content += memories_str
            return msgs_copy

        except Exception as e:
            raise Mem1Exception(
                message="Error while loading memory",
                error=str(e),
            )
