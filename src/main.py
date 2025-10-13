import asyncio

from src.assistant import Assistant
from src.database import DBStore
from src.deps.langfuse import init_langfuse
from src.inference import inference

async def main():
    await DBStore.init_db()
    init_langfuse()
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
    response = await assistant.reply(query)
    print(f"\n> {response}")


if __name__ == "__main__":
    asyncio.run(main())
