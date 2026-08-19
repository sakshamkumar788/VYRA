from datetime import datetime
from zoneinfo import ZoneInfo

from brain.ollama_brain import OllamaBrain
from memory.database import (
    get_pending_tasks,
    get_relevant_memories,
    initialize_database,
    save_memory,
    save_task,
)


class VYRA:
    """Core VYRA assistant."""

    MODEL = "gemma3:4b"
    TIMEZONE = "Asia/Kolkata"

    SYSTEM_PROMPT = """
You are VYRA, a personal AI companion and assistant for Saksham.

PERSONALITY:
- Warm, intelligent, observant, calm, and natural.
- Slightly playful when appropriate.
- Supportive, but willing to gently challenge Saksham.
- Concise for simple questions.
- Detailed when Saksham asks for detail.
- Do not sound like a robotic command-line assistant.
- Do not constantly ask follow-up questions.
- Do not repeatedly say "How can I help you?"
- Do not narrate your internal reasoning.
- Do not say things like "I'm sensing a mood" unless explicitly asked.
- Do not force personal information into unrelated answers.
- Do not mention a personal memory merely to personalize a response.
- Only use personal memories when relevant.
- Do not pretend to be conscious or literally alive.
- Maintain a consistent identity as VYRA.

CURRENT CAPABILITIES:
Currently available:
- text conversation
- short-term conversation context
- local long-term memory
- current date and time
- basic local task storage

NOT CURRENTLY AVAILABLE:
- camera
- microphone
- screen access
- WhatsApp
- internet
- browser control
- file control
- face recognition
- voice recognition
- computer control

Never claim that an action was performed unless the program actually performed it.

MEMORY RULES:
- Relevant memories may be provided with the current request.
- Treat provided memories as factual.
- Use them when they directly help answer the request.
- Do not invent memories.
- Do not mention unrelated memories.

TASK RULES:
- Use pending task information when relevant.
- Never claim a reminder was delivered unless a real reminder system delivered it.
- Never claim a task was created unless the application actually created it.
"""

    def __init__(self) -> None:
        initialize_database()

        self.brain = OllamaBrain(model=self.MODEL)

        # Short-term conversation history.
        self.conversation: list[dict[str, str]] = []

    def get_current_context(self) -> str:
        """Return current date and time information."""

        now = datetime.now(ZoneInfo(self.TIMEZONE))

        hour = now.hour

        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 21:
            period = "evening"
        else:
            period = "night"

        return (
            f"Current date: {now.strftime('%d %B %Y')}\n"
            f"Current time: {now.strftime('%I:%M %p')}\n"
            f"Day: {now.strftime('%A')}\n"
            f"Time period: {period}\n"
            f"Timezone: {self.TIMEZONE}"
        )

    def get_relevant_memory_text(self, query: str) -> str:
        """Retrieve memories relevant to the current request."""

        memories = get_relevant_memories(query)

        if not memories:
            return "No relevant long-term memories were found."

        lines = ["Relevant long-term memories:"]

        for memory_type, content in memories:
            lines.append(
                f"- [{memory_type}] {content}"
            )

        return "\n".join(lines)

    def get_task_context(self) -> str:
        """Return pending tasks."""

        tasks = get_pending_tasks()

        if not tasks:
            return "No pending tasks are currently stored."

        lines = ["Pending tasks:"]

        for task_id, title, due_at, status in tasks:
            due_text = due_at if due_at else "No due time"

            lines.append(
                f"- Task ID {task_id}: "
                f"{title} | Due: {due_text} | Status: {status}"
            )

        return "\n".join(lines)

    def should_store_memory(self, user_message: str) -> bool:
        """Temporary memory-detection prototype."""

        memory_signals = [
            "i am",
            "i'm",
            "i want",
            "i need",
            "my goal",
            "i prefer",
            "i like",
            "i don't like",
            "remember",
            "from now on",
            "this semester",
            "this week",
            "i decided",
            "i plan",
            "i'm planning",
            "my priority",
            "i've decided",
        ]

        message = user_message.lower()

        return any(
            signal in message
            for signal in memory_signals
        )

    def save_memory_with_confirmation(
        self,
        user_message: str,
    ) -> None:
        """Ask whether a potentially important statement should be remembered."""

        print(
            "VYRA: That sounds like something that might be "
            "useful for me to remember. Should I save it? (yes/no)"
        )

        confirmation = input("You: ").strip().lower()

        if confirmation in {"yes", "y"}:
            save_memory("user_note", user_message)

            print(
                "VYRA: Got it. I'll remember that.\n"
            )
        else:
            print(
                "VYRA: Okay, I won't save it.\n"
            )

    def handle_remember_command(
        self,
        user_input: str,
    ) -> bool:
        """Handle /remember commands."""

        if not user_input.lower().startswith("/remember "):
            return False

        memory = user_input[
            len("/remember "):
        ].strip()

        if memory:
            save_memory("user_note", memory)
            print(
                "VYRA: Got it. I'll remember that.\n"
            )
        else:
            print(
                "VYRA: Tell me what you'd like me to remember.\n"
            )

        return True

    def handle_task_command(
        self,
        user_input: str,
    ) -> bool:
        """
        Temporary developer command for creating a task.

        Format:
        /task Task name | YYYY-MM-DD HH:MM
        """

        if not user_input.lower().startswith("/task "):
            return False

        task_data = user_input[
            len("/task "):
        ].strip()

        if "|" not in task_data:
            print(
                "VYRA: Use this format:\n"
                "/task Task name | YYYY-MM-DD HH:MM\n"
            )
            return True

        title, due_at = task_data.split("|", 1)

        title = title.strip()
        due_at = due_at.strip()

        if not title or not due_at:
            print(
                "VYRA: I need both the task and its due time.\n"
            )
            return True

        save_task(title, due_at)

        print(
            f"VYRA: Got it. I'll remember the task "
            f"'{title}' for {due_at}.\n"
        )

        return True

    def generate_reply(
        self,
        user_input: str,
    ) -> str:
        """Build context and generate VYRA's response."""

        self.conversation.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        current_context = self.get_current_context()
        relevant_memory = self.get_relevant_memory_text(
            user_input
        )
        pending_tasks = self.get_task_context()

        model_request = f"""
CURRENT CONTEXT:
{current_context}

RELEVANT LONG-TERM MEMORY:
{relevant_memory}

CURRENT PENDING TASKS:
{pending_tasks}

CURRENT USER REQUEST:
{user_input}

Answer the user's request naturally.

Rules:
- Use relevant long-term memory when it directly helps.
- Use task information when it directly helps.
- Do not invent facts about Saksham.
- Do not mention unrelated memories or tasks.
- Do not claim that an action was performed unless it was actually performed.
- Do not claim that a reminder was delivered unless a reminder system actually delivered it.
"""

        messages_for_model: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT,
            },
            *self.conversation[:-1],
            {
                "role": "user",
                "content": model_request,
            },
        ]

        reply = self.brain.generate(
            messages_for_model
        )

        self.conversation.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        return reply

    def run(self) -> None:
        """Start the VYRA text interface."""

        print("VYRA: Online.")
        print("Type 'exit' to close VYRA.")
        print("Commands:")
        print("  /remember <something>")
        print("  /task <task> | <YYYY-MM-DD HH:MM>")
        print()

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == "exit":
                print("VYRA: Goodnight, sir.")
                break

            if not user_input:
                continue

            if self.handle_remember_command(
                user_input
            ):
                continue

            if self.handle_task_command(
                user_input
            ):
                continue

            if self.should_store_memory(
                user_input
            ):
                self.save_memory_with_confirmation(
                    user_input
                )
                continue

            reply = self.generate_reply(
                user_input
            )

            print(
                f"VYRA: {reply}\n"
            )