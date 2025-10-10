from src.inference import inference

def main():
    print(f"Application started!")

if __name__ == "__main__":
    main()
    print("\n")
    user_query = input("Enter you query: ")
    result = inference(query=user_query)
    print(f"\n> {result}")
