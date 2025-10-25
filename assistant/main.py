import asyncio
from langfuse import observe

from assistant.assistant import Assistant
from assistant.deps.langfuse import init_langfuse
from assistant.utils.logger import configure_logging
from infra.database import DBStore
from infra.redis import RedisClient

@observe()
async def main():
    configure_logging()
    await DBStore.init_db()
    init_langfuse()
    RedisClient.connect()
    assistant = Assistant()

    print(f"Application started!")

    '''
    stop_words = ["exit"]
    while True:
        print("\n")
        user_query = input("Enter your query (Type 'exit' to quit): ")
        if user_query.lower() in stop_words:
            break
        print(f"\nThinking...\n")
        result = inference(query=user_query)
        print(f"\n> {result}")
    '''

    user_query = input("Enter your query (Type '/exit' to quit): ")
    print(f"\nThinking...\n")
    response = await assistant.reply(user_query)
    print(f"\n> {response}")


if __name__ == "__main__":
    asyncio.run(main())
