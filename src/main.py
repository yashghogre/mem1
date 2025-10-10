from src.inference import inference

def main():
    print(f"Application started!")

if __name__ == "__main__":
    main()
    result = inference(query="Who is the prime minister of India?")
    print(result)
