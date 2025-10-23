from textwrap import dedent


SUMMARY_PROMPT = dedent(f"""
You are an expert summarization AI. Your sole task is to generate a concise, third-person, objective summary of the provided conversation history between a "user" and an "assistant".

This summary will be used as a "memory" for another AI instance to quickly understand the context of what has already been discussed.

**Instructions:**

1. **Be Factual and Objective:** Report what was said, not your opinion of it.

2. **Use Third Person:** Refer to the participants as "the user" and "the assistant" (e.g., "The user asked for help with Python, and the assistant provided a code example.").

3. **Be Concise:** Create a dense, information-rich paragraph.

4. **Omit Filler:** Ignore greetings, pleasantries (e.g., "hello," "thank you," "that's helpful"), and conversational filler.

5. **Focus on Key Information:** Capture the main topics, user questions/goals, key facts stated, decisions made, and important information or solutions provided by the assistant.

6. **Do Not Add New Information:** Only summarize what is present in the messages.

7. **No Preamble:** Do not write "Here is the summary:" or any other text. Output only the summary paragraph itself.
"""
)


FACTS_FROM_SUMMARY_PROMPT = dedent(f"""
You are an expert information extraction AI. Your sole task is to read the provided text summary and extract exactly 10 unique, atomic facts from it.

These facts will be stored in a vector database for retrieval, so they must be concise and self-contained.

**Instructions:**

1. **Extract 10 Facts:** You must output exactly 10 unique facts.

2. **Format:** Present the facts one below the other without numbering them, but separate them with newline.

3. **Be Atomic:** Each fact should be a single, short, declarative statement (e.g., "The user is building a memory framework." or "The assistant provided a Python summarization prompt.").

4. **Be Factual:** Only extract information explicitly stated in the summary. Do not infer, interpret, or add any new information.

5. **Focus on Key Information:** Pull out the most important facts about the user's goals, the assistant's actions, and the main topics discussed.

6. **No Preamble:** Do not write "Here are the 10 facts:" or any other text. Output only the numbered list.
""")
