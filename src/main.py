import asyncio

from src.database import DBStore
from src.deps.langfuse import init_langfuse
from src.inference import inference

async def main():
    await DBStore.init_db()
    init_langfuse()

    print(f"Application started!")
    stop_words = ["exit"]
    while True:
        print("\n")
        user_query = input("Enter you query (Type 'exit' to quit): ")
        if user_query.lower() in stop_words:
            break
        print(f"\nThinking...\n")
        result = inference(query=user_query)
        print(f"\n> {result}")

if __name__ == "__main__":
    asyncio.run(main())
