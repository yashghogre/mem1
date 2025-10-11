from src.inference import inference

def main():
    print(f"Application started!")

if __name__ == "__main__":
    main()
    stop_words = ["exit"]
    while True:
        print("\n")
        user_query = input("Enter you query (Type 'exit' to quit): ")
        if user_query.lower() in stop_words:
            break
        print(f"\nThinking...\n")
        result = inference(query=user_query)
        print(f"\n> {result}")
