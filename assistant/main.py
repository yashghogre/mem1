import asyncio
from langfuse import observe
import logging

from assistant.assistant import Assistant
from assistant.deps.langfuse import init_langfuse
from assistant.utils.logger import configure_logging
from assistant.utils.special_commands import handle_commands, SPECIAL_COMMANDS
from infra.database import DBStore
from infra.vector_db import VectorSearch


configure_logging()

logger = logging.getLogger(__name__)

@observe()
async def main():
    await DBStore.init_db()
    await VectorSearch.setup()
    # init_langfuse()
    assistant = Assistant()

    print(f"Application started!")
    logger.debug(f"Application started. DB and VectorSearch are setup.")
    
    while True:
        user_query = input("Enter your query (Type '/exit' to quit): ")
        if user_query.lower().strip() in [sp_cmd.value for sp_cmd in SPECIAL_COMMANDS]:
            return await handle_commands(user_query)
        print(f"\nThinking...\n")
        response = await assistant.reply(user_query)
        print(f"\n> {response}")


if __name__ == "__main__":
    asyncio.run(main())
