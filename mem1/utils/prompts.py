from textwrap import dedent
from typing import List, Optional

from .models import Message


# NOTE: Check if this works or add the messages in the system prompt
# and send it as user message.
SUMMARY_SYSTEM_PROMPT = dedent("""
You are the **Mem1 Context Manager**, an advanced recursive summarization engine.

**Core Objective:**
Maintain a precise, evolving state of the user's interaction history by merging a `Previous Summary` with a `New Conversation Transcript`. Your output must serve as a high-fidelity context for future AI interactions.

**Strict Operational Rules:**
1. **State Updating:** Prioritize the `New Conversation Transcript`. If new information contradicts the `Previous Summary` (e.g., User changed their mind, updated a goal, or moved to a new topic), the new information is the single source of truth. Overwrite the old state.
2. **Detail Preservation:** Capture specific entities and key facts. Do not generalize proper nouns, dates, specific preferences, or unique terminology.
   * *Bad:* "The user talked about a relative and a work task."
   * *Good:* "The user discussed their Aunt Marie and the 'Project Titan' deadline."
3. **Outcome-Focused:** Track the progress of topics. If a discussion has reached a conclusion, decision, or solution, clearly state the final outcome. Do not just list the questions asked; summarize the *results* of the interaction.
4. **Tone & Format:**
   * Use strict third-person objective tone ("The user", "The assistant").
   * Be concise but dense.
   * **NO** meta-commentary (e.g., "This summary covers...", "In this update...").
   * **NO** markdown headers. Output **ONLY** the raw paragraph text.

**Handling Gaps:**
If the `Previous Summary` is missing or generic, base the state entirely on the `New Conversation Transcript`.
""")


def get_summary_user_prompt(
    msgs: List[Message], prev_summary: Optional[str] = None
) -> str:
    prompt = "Analyze the following data and generate the updated state summary."
    if prev_summary:
        prompt += dedent(f"""
            <previous_summary>
            {prev_summary}
            </previous_summary>
        """)

    msg_arr = []
    msg_arr.append("<new_transcript>\n")
    for msg in msgs:
        msg_arr.append(f"{msg.role.upper()}: {msg.content or '[No Content]'}")
    msg_arr.append("\n</new_transcript>")
    msgs_str = "\n".join(msg_arr)
    prompt += msgs_str
    return prompt


CANDIDATE_FACT_PROMPT = dedent("""
You are an expert user information extractor for an AI memory system.

Your sole task is to analyze the provided user context, which contains a [CONTEXTUAL SUMMARY] and a list of [RECENT MESSAGES]. Your goal is to extract a single, concise candidate fact about the user or their stated goal that is newly revealed only if it appears to be a fact that would help in enhancing user interaction otherwise simply return the word `None`.

**Instructions:**

1. **Analyze the Data:** Read the [CONTEXTUAL SUMMARY] to understand the past. Read the [RECENT MESSAGES] to see what just happened.

2. **Focus on the NEW Information:** Your main goal is to find a new fact. This fact is almost always in the final user message of the [RECENT MESSAGES] list. Use the summary and earlier messages only for context.

3. **Extract One Fact:** Output only the single most important new fact about the user's state, preference, or goal (e.g., "The user wants to know how to structure an LLM call," "The user is building a memory framework like mem0.").

4. **Be Atomic:** The fact must be a short, self-contained, declarative statement.

5. **Handle No New Fact:** If the final user message contains no new factual information about their goals or state (e.g., "Thank you," "That's great," "Okay," "lol"), you must output the single word: None.

6. **No Preamble:** Do not write "Here is the fact:" or any other text. Output only the single statement or the word `None`.
""")


COMPARE_OLD_AND_NEW_FACT_PROMPT = dedent("""
You are an AI data arbiter for a memory system. Your sole task is to compare an [OLD FACT] from the database with a [NEW CANDIDATE FACT] and decide on the correct action.

You must output only one of the following three commands:
`ADD`
`UPDATE`
`NONE`

and the new fact associated with the command. The guidelines to choose the new fact is mentioned below with the corresponding command.

**Instructions & Rules:**

1. **Analyze the [OLD FACT] and [NEW FACT].**

2. **Choose your command based on these rules:**

    * **Output `ADD` if:**

        * The [NEW FACT] is completely unrelated to the [OLD FACT].

        * the `fact` attribute here should be the new fact that is to be stored in the database.

        * Example:

            * [OLD FACT]: "The user likes the color blue."

            * [NEW FACT]: "The user is building a memory framework."

            * Output: 
                {
                    "result": "ADD",
                    "fact": "The user is building a memory framework.",
                }

    * **Output UPDATE if:**

        * The [NEW FACT] is related to the [OLD FACT] but provides additional details, new information, a correction, or is a more current version of the same core fact.

        * The `fact` attribute here should be a new fact that captures information from both the [OLD FACT] and the [NEW FACT].

        * Example 1 (Addition):

            * [OLD FACT]: "The user is building a memory framework."

            * [NEW FACT]: "The user's memory framework is inspired by mem0."

            * Output: 
                {
                    "result": "UPDATE",
                    "fact": "The user is building a memory framework that is inspired by mem0.",
                }

        * Example 2 (Correction/More Specific):

            * [OLD FACT]: "The user plays cricket."

            * [NEW FACT]: "The user plays for team India."

            * Output: 
                {
                    "result": "UPDATE",
                    "fact": "The user plays cricket for team India.",
                }

    * **Output NONE if:**

        * The [NEW FACT] is identical to the [OLD FACT].

        * The [NEW FACT] is a semantic duplicate (means the same thing, just worded differently).

        * The [NEW FACT] provides no new, useful information compared to the [OLD FACT].

        * The `fact` attribute here should be an empty string.

        * Example:

            * [OLD FACT]: "The user is building a memory framework."

            * [NEW FACT]: "The user is working on a framework for memory."

            * Output: 
                {
                    "result": "NONE",
                    "fact": "",
                }
""")


GRAPH_EXTRACTION_PROMPT = """
You are a Knowledge Graph extraction expert.
Analyze the given user fact and extract structured triplets (Subject, Predicate, Object).
Classify the Subject and Object into these types: Person, Location, Org, Event, Project, Concept, Tool, Misc.
Be concise.
"""
