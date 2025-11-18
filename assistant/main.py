import asyncio
import logging
import sys

from assistant.assistant import Assistant
# from assistant.deps.langfuse import init_langfuse
from assistant.utils.logger import configure_logging
from assistant.utils.special_commands import handle_commands, SPECIAL_COMMANDS

from .infra.database import DBStore
from .infra.vector_db import VectorSearch


configure_logging()
logger = logging.getLogger(__name__)

READY_PROMPT = "User>"

# @observe()
async def main():
    await DBStore.init_db()
    await VectorSearch.setup()
    # init_langfuse()  # Uncomment when ready to use Langfuse
    assistant = Assistant()

    print("Application started!", file=sys.stderr)
    logger.debug("Application started. DB and VectorSearch are setup.")
    
    print(READY_PROMPT, flush=True)
    
    while True:
        try:
            user_query = sys.stdin.readline()
            
            if not user_query:
                logger.info("EOF received, shutting down.")
                break
                
            user_query = user_query.strip()
            
            if not user_query:
                print(READY_PROMPT, flush=True)
                continue
            
            if user_query.lower() in [sp_cmd.value for sp_cmd in SPECIAL_COMMANDS]:
                await handle_commands(user_query)
                break
            
            print("Thinking...", file=sys.stderr, flush=True)
            
            response = await assistant.reply(user_query)
            
            print(response, flush=True)
            
            print(READY_PROMPT, flush=True)

        except EOFError:
            logger.info("StdIn closed, shutting down.")
            break
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
            break
            
        except Exception as e:
            logger.critical(f"A critical error occurred: {e}", exc_info=True)
            print(f"Critical error: {e}", file=sys.stderr, flush=True)
            print(READY_PROMPT, flush=True)
            
    logger.info("Application shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
