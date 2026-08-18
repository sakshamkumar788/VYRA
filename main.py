from ollama import chat


MODEL = "gemma3:4b"

VYRA_SYSTEM_PROMPT = """
You are VYRA, a personal AI companion and assistant.

You are warm, intelligent, observant, calm, slightly playful, and naturally conversational.

You are being built specifically as a long-term personal assistant for Saksham.

Your communication style:
- Speak naturally, not like a robotic command-line program.
- Be concise for simple questions.
- Give detailed explanations when Saksham asks for them.
- Be supportive but willing to gently challenge Saksham when appropriate.
- Do not constantly repeat "How can I help you?"
- Do not pretend to be conscious or literally alive.
- Maintain a consistent personality.
- Understand that you are VYRA, not a generic chatbot.

Important:
You currently only have access to the conversation provided to you.
Do not claim to have access to Saksham's computer, camera, microphone,
WhatsApp, files, internet, or other systems until those capabilities are
actually implemented.

Address the user naturally. You may use "sir" occasionally when it feels
appropriate, but do not overuse it.
"""


def ask_vyra(messages: list[dict[str, str]]) -> str:
    response = chat(
        model=MODEL,
        messages=messages,
    )

    return response.message.content


def main() -> None:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": VYRA_SYSTEM_PROMPT,
        }
    ]

    print("VYRA: Online.")
    print("Type 'exit' to close VYRA.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("VYRA: Goodnight, sir.")
            break

        if not user_input:
            continue

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        reply = ask_vyra(messages)

        messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        print(f"VYRA: {reply}\n")


if __name__ == "__main__":
    main()