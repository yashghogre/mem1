import asyncio
from textwrap import dedent
from typing import List, Optional

from infra.database import DBStore
from infra.database.schema import Message
from infra.graph_db import GraphDB
from infra.inference import Inference
from infra.redis import RedisClient
from infra.vector_db import VectorSearch

from .utils.enums import FactComparisonResult
from .utils.prompts import (
    SUMMARY_PROMPT,
    CANDIDATE_FACT_PROMPT,
    COMPARE_OLD_AND_NEW_FACT_PROMPT,
)


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
        *
        max_memories_in_vector_db: Optional[int] = 10,
        message_interval_for_summary: Optional[int] = 5,
        max_messages_for_new_fact: Optional[int] = 10,
    ):
        self.max_memories_in_vector_db = max_memories_in_vector_db
        self.message_interval_for_summary = message_interval_for_summary
        self.max_messages_for_new_fact = max_messages_for_new_fact


    async def _summarize_messages(self, messages: List[Message], prev_summary: Optional[str] = None) -> str:
        try:
            msgs = deepcopy(messages)
            msgs = msgs[-(self.max_messages_for_new_fact):]
            if prev_summary is None:
                prev_summary = "No Previous Summary Available."
            summary_prompt = SUMMARY_PROMPT.format(PREVIOUS_SUMMARY=prev_summary)
            sys_msg = Message(
                role="system",
                content=SUMMARY_PROMPT,
            )
            msgs.insert(0, sys_msg)

            return await Inference.run(msgs)

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
            msgs = msgs[-(self.max_messages_for_new_fact):]
            sys_msg = Message(
                role="system",
                content=CANDIDATE_FACT_PROMPT,
            )
            query_msg = self._form_user_msg_for_candidate_fact(msgs, summary)
            msgs = [sys_msg, query_msg]
            return await Inference.run(msgs)

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
            user_msg = Message(
                role="user",
                content=usr_msg_content,
            )
            msgs = [sys_msg, user_msg]
            return await Inference.run(msgs)

        except Exception as e:
            raise Mem1Exception(
                message="Error while comparing facts.",
                error=str(e),
            )


    async def _add_fact(self, fact: str):
        try:
            all_facts = await VectorSearch.retrieve_all_points()
            if len(all_facts) > self.max_memories_in_vector_db:
                await VectorSearch.find_oldest_fact_and_delete()

            await VectorSearch.store_point(fact)

        except Exception as e:
            raise Mem1Exception(
                message="Error while adding a new fact.",
                error=str(e),
            )


    async def _update_fact(self, new_fact: str, old_fact):
        try:
            await VectorSearch.delete_point(old_fact)
            await VectorSearch.store_point(new_fact)

        except Exception as e:
            raise Mem1Exception(
                message="Error while updating old fact.",
                error=str(e),
            )
        

    async def process_memory(self, messages: List[Message]):
        try:
            user_msg_count = self._count_user_messages(messages)
            prev_chat_summary = await DBStore.get_chat_summary()
            if (user_msg_count - 1) % self.message_interval_for_summary == 0 or prev_chat_summary is None:
                chat_summary = self._summarize_messages(messages=messages, prev_summary=prev_chat_summary)
                await DBStore.store_chat_summary(summary=chat_summary)
            else:
                chat_summary = prev_chat_summary

            candidate_fact = await self._find_candidate_fact(messages, chat_summary)
            #TODO: Verify what `retrieve_point` returns in case of no point in DB.
            # Make changes accordingly.
            old_fact_point = await VectorSearch.retrieve_point(candidate_fact) or "No previous facts"
            if not isinstance(old_fact_point, str):
                old_fact_point = old_fact_point[0]
                old_fact = old_fact_point.payload.get("text")
            else:
                old_fact = "No previous facts"

            fact_comp_res = await self._compare_facts(old_fact, candidate_fact)

            match fact_comp_res.strip():
                case FactComparisonResult.ADD.value:
                    await self._add_fact(candidate_fact)

                case FactComparisonResult.UPDATE.value:
                    await self._update_fact(candidate_fact, old_fact_point)

                case FactComparisonResult.NONE.value:
                    pass

                case _:
                    raise Mem1Exception(
                        message="Error in LLM output while checking comparison results",
                        error=f"The LLM returned {fact_comp_res.strip()} which does not match any of `ADD`, `UPDATE` or `NONE`.",
                        suggestion="This is a LLM side error. Alter prompt for better results.",
                    )

            
        except Exception as e:
            raise Mem1Exception(message="Error while adding memory.", error=str(e))


    async def load_memory(self):
        raise NotImplementedError(f"Load Memory is not yet implemented.")
