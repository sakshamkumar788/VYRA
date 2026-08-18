from ollama import chat


def main() -> None:
    response = chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "user",
                "content": "Hello. Introduce yourself in one sentence."
            }
        ],
    )

    print(response.message.content)


if __name__ == "__main__":
    main()