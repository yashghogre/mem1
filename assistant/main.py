import asyncio
from langfuse import observe

from assistant.assistant import Assistant
from assistant.deps.langfuse import init_langfuse
from assistant.utils.logger import configure_logging
from infra.database import DBStore
from infra.vector_db import VectorSearch

@observe()
async def main():
    configure_logging()
    await DBStore.init_db()
    await VectorSearch.setup()
    init_langfuse()
    assistant = Assistant()

    print(f"Application started!")

    user_query = input("Enter your query (Type '/exit' to quit): ")
    print(f"\nThinking...\n")
    response = await assistant.reply(user_query)
    print(f"\n> {response}")


if __name__ == "__main__":
    asyncio.run(main())
