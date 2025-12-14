import asyncio
from beanie import Document
from copy import deepcopy
import httpx
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncDriver
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from textwrap import dedent
from typing import List, Optional

from assistant.infra.database.schema import Message
# TODO: Completely remove the MongoDB dependency for summary
# of figure out a way to include this schema in the
# already intialized MongoDB client.

from .infra.database import DatabaseUtils
from .infra.embedder import EmbedderUtils
from .infra.graph_db import GraphDBUtils

from .infra.vectordb import VectorDBUtils
from .utils.enums import FactComparisonResult, NoFactStrings
from .utils.models import (
    CandidateFactsModel,
    FactsComparisonResultModel,
    GraphTriplets,
    KnowledgeGraphExtraction,
    Message,
)
from .utils.prompts import (
    get_summary_user_prompt,
    SUMMARY_SYSTEM_PROMPT,
    CANDIDATE_FACT_PROMPT,
    COMPARE_OLD_AND_NEW_FACT_PROMPT,
    GRAPH_EXTRACTION_PROMPT,
)


logger = logging.getLogger(__name__)


class Mem1Exception(Exception):
    def __init__(
        self,
        error: str,
        message: Optional[str] = None,
        suggestion: Optional[str] = None,
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
        database_client: AsyncIOMotorClient,  # NOTE: Will remove this once I figure out a more efficient way to store the summary.
        database_collection: Document,
        graph_db_client: AsyncDriver,
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
        self.graph_db_client = graph_db_client

        self.max_memories_in_vector_db = max_memories_in_vector_db
        self.message_interval_for_summary = message_interval_for_summary
        self.max_messages_for_new_fact = max_messages_for_new_fact

        self.db_utils = DatabaseUtils(
            db_client=self.database_client,
            collection=self.database_collection,
        )
        self.embedder = EmbedderUtils(embedder_client=self.embedder_client)
        self.graphdb_utils = GraphDBUtils(driver=self.graph_db_client)
        self.vectordb_utils = VectorDBUtils(
            vectordb_client=self.vector_db_client,
            vectordb_collection=self.vector_db_collection,
            embedder=self.embedder,
        )

    async def _summarize_messages(
        self, messages: List[Message], prev_summary: Optional[str] = None
    ) -> str:
        try:
            logger.info(f"Summarize messages called!")
            msgs = deepcopy(messages)
            msgs = msgs[-(self.max_messages_for_new_fact) :]
            summary_prompt = SUMMARY_SYSTEM_PROMPT
            sys_msg = Message(
                role="system",
                content=summary_prompt,
            )
            usr_msg = Message(
                role="user",
                content=get_summary_user_prompt(msgs, prev_summary),
            )
            final_msgs = [sys_msg, usr_msg]
            logger.debug(f"messages for summary: {final_msgs}")

            response = await self.chat_client.chat.completions.create(
                model=self.model_name,
                messages=[final_msg.model_dump() for final_msg in final_msgs],
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Mem1Exception(
                message="Error while summarizing messages.", error=str(e)
            )

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
            user_msg.append(f"{msg.role.upper()}: {msg.content}")
        final_user_msg = Message(
            role="user",
            content="\n".join(user_msg),
        )
        return final_user_msg

    async def _find_candidate_facts(
        self, messages: List[Message], summary: str
    ) -> List:
        try:
            msgs = messages[-(self.max_messages_for_new_fact) :]
            sys_msg = Message(
                role="system",
                content=CANDIDATE_FACT_PROMPT,
            )
            query_msg = self._form_user_msg_for_candidate_fact(msgs, summary)
            msgs_raw = [sys_msg, query_msg]
            msgs_to_send = [msg_raw.model_dump() for msg_raw in msgs_raw]

            response = await self.chat_client.beta.chat.completions.parse(
                model=self.model_name,
                messages=msgs_to_send,
                response_format=CandidateFactsModel,
            )
            result: CandidateFactsModel = response.choices[0].message.parsed
            logger.info(f"candidate facts: {result}")
            return result.facts

        except Exception as e:
            raise Mem1Exception(
                message="Error while finding candidate fact.",
                error=str(e),
            )

    async def _compare_facts(self, old_fact: str, new_fact: str):
        try:
            NO_FACT_STR = [res.value for res in NoFactStrings]

            if old_fact in NO_FACT_STR and new_fact in NO_FACT_STR:
                return FactsComparisonResultModel(
                    result=FactComparisonResult.NONE,
                    fact="",
                )
            elif old_fact in NO_FACT_STR:
                return FactsComparisonResultModel(
                    result=FactComparisonResult.ADD,
                    fact=new_fact,
                )
            elif new_fact in NO_FACT_STR:
                return FactsComparisonResultModel(
                    result=FactComparisonResult.NONE,
                    fact="",
                )
            else:
                sys_msg = Message(
                    role="system",
                    content=COMPARE_OLD_AND_NEW_FACT_PROMPT,
                )
                usr_msg_content = (
                    f"\nOLD FACT:\n{old_fact}\n\nNEW CANDIDATE FACT:\n{new_fact}"
                )
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

    async def _resolve_entity(self, extracted_name: str, entity_type: str) -> str:
        if await self.graphdb_utils.find_node_by_name(extracted_name):
            return extracted_name

        candidates = await self.graphdb_utils.search_similar_nodes(extracted_name)
        if not candidates:
            return extracted_name

        candidate_names = [c["name"] for c in candidates]

        try:
            prompt = dedent(f"""
            Resolve Entity.
            Input: "{extracted_name}" ({entity_type}).
            Existing Options: {candidate_names}.
            Does Input refer to an option? Return EXACT option name or "NEW".
            """)
            response = await self.chat_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            decision = response.choices[0].message.content.strip()
            return decision if decision in candidate_names else extracted_name

        except Exception as e:
            logger.error(f"Exception while resolving entity: {str(e)}")
            return extracted_name

    async def _extract_knowledge_graph(self, fact: str) -> List[GraphTriplets]:
        try:
            sys_msg = Message(role="system", content=GRAPH_EXTRACTION_PROMPT)
            user_msg = Message(role="user", content=f"FACT: {fact}")

            response = await self.chat_client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[sys_msg, user_msg],
                response_format=KnowledgeGraphExtraction,
            )
            return response.choices[0].message.parsed.triplets

        except Exception as e:
            logger.error(f"Error extracting graph data: {str(e)}")
            return []

    async def _update_graph_memory(self, fact: str):
        triplets = await self._extract_knowledge_graph(fact)
        for t in triplets:
            subj_name = await self._resolve_entity(t.subject, t.subject_type)
            obj_name = await self._resolve_entity(t.object, t.object_type)

            await self.graphdb_utils.add_node(
                parameters={"name": subj_name},
                entity=t.subject_type,
            )
            await self.graphdb_utils.add_node(
                parameters={"name": obj_name},
                entity=t.object_type,
            )
            await self.graphdb_utils.add_relationship(
                node_1_name=subj_name,
                node_2_name=obj_name,
                relationship=t.predicate,
                node_1_entity=t.subject_type,
                node_2_entity=t.object_type,
            )
            logger.info(f"Updated GraphDB with {len(triplets)} relationships.")

    async def _retrieve_graph_context(self, user_query: str) -> str:
        keywords = user_query.split()
        context_lines = []

        for word in keywords:
            if len(word) > 3:
                data = await self.graphdb_utils.get_2_hop_neighborhood(word, limit=5)
                for rec in data:
                    line = f"{rec['source']} {rec['rel1']} {rec['intermediate']}"
                    if rec["target"]:
                        line += f" which {rec['rel2']} {rec['target']}"
                    context_lines.append(line)

        return "\n".join(set(context_lines))

    async def process_memory(self, messages: List[Message]):
        try:
            user_msg_count = self._count_user_messages(messages)
            if (user_msg_count - 1) % self.max_messages_for_new_fact == 0:  # type: ignore
                return messages

            prev_chat_summary = await self.db_utils.get_chat_summary()
            if prev_chat_summary is not None:
                prev_chat_summary = prev_chat_summary.summary

            if (
                user_msg_count - 1
            ) % self.message_interval_for_summary == 0 or prev_chat_summary is None:  # type: ignore
                chat_summary = await self._summarize_messages(
                    messages=messages, prev_summary=prev_chat_summary
                )
                await self.db_utils.store_chat_summary(summary=chat_summary)
            else:
                chat_summary = prev_chat_summary

            candidate_facts = await self._find_candidate_facts(messages, chat_summary)

            for candidate_fact in candidate_facts:
                old_fact_point = (
                    await self.vectordb_utils.retrieve_point(text=candidate_fact)
                    or NoFactStrings.NO_PREV_FACT.value
                )
                if not isinstance(old_fact_point, str):
                    logger.debug(f"old_fact_point: {old_fact_point}")
                    old_fact = old_fact_point.payload.get("text")
                else:
                    old_fact = NoFactStrings.NO_PREV_FACT.value

                fact_comp_res = await self._compare_facts(old_fact, candidate_fact)
                comparison_res = fact_comp_res.result.strip()
                comparison_fact = fact_comp_res.fact.strip()

                match comparison_res:
                    case FactComparisonResult.ADD.value:
                        logger.info("ADDING NEW FACT")
                        await self._add_fact(comparison_fact)
                        await self._update_graph_memory(comparison_fact)

                    case FactComparisonResult.UPDATE.value:
                        logger.info("UPDATING EXISTING FACT")
                        await self._update_fact(comparison_fact, old_fact_point)
                        await self._update_graph_memory(comparison_fact)

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
            raise Mem1Exception(message="Error while processing memory.", error=str(e))

    async def load_memory(self, messages: List[Message]) -> List[Message]:
        try:
            msgs_copy = deepcopy(messages)
            sys_msg = msgs_copy[0]
            if sys_msg.role != "system":
                logger.error(
                    "Error while checking system message while loading memory. System message not found in the context."
                )
                raise Mem1Exception(
                    message="Error while checking system message.",
                    error="System message not found in the context.",
                    suggestion="Make sure to include system message in the context.",
                )

            user_memories = await self.vectordb_utils.retrieve_all_points()
            if user_memories is None:
                return msgs_copy

            memories_arr = [mem.payload.get("text") for mem in user_memories]
            memories_arr.insert(
                0, "\n<Memory-Block>\n**Here are some long-term memories of the user:**"
            )
            memories_arr.append("</Memory-Block>")
            memories_str = "\n".join(memories_arr)

            last_user_msg = next(
                (m.content for m in reversed(messages) if m.role == "user"), ""
            )
            graph_context = await self._retrieve_graph_context(last_user_msg)
            if graph_context:
                memories_str += graph_context

            msgs_copy[0].content += memories_str
            return msgs_copy

        except Exception as e:
            raise Mem1Exception(
                message="Error while loading memory",
                error=str(e),
            )
