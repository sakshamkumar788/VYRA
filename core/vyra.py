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

from tools.calculator import calculate
from tools.registry import Tool, ToolRegistry
from tools.router import ToolRouter
from tools.weather import get_weather


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
- Only use personal memories when they are relevant.
- Do not pretend to be conscious or literally alive.
- Maintain a consistent identity as VYRA.

CURRENT CAPABILITIES:
Currently available:
- text conversation
- short-term conversation context
- local long-term memory
- current date and time
- basic local task storage
- calculator tool
- weather tool

NOT CURRENTLY AVAILABLE:
- camera
- microphone
- screen access
- WhatsApp
- browser control
- file control
- face recognition
- voice recognition
- computer control

Never claim that an action was performed unless the program actually
performed it.

MEMORY RULES:
- Relevant memories may be provided with the current request.
- Treat provided memories as factual.
- Use them when they directly help answer the request.
- Do not invent memories.
- Do not mention unrelated memories.

TASK RULES:
- Use pending task information when relevant.
- Never claim a reminder was delivered unless a real reminder system
  delivered it.
- Never claim a task was created unless the application actually
  created it.
"""

    def __init__(self) -> None:
        initialize_database()

        # ---------------------------------------------------------
        # Brain
        # ---------------------------------------------------------
        self.brain = OllamaBrain(
            model=self.MODEL
        )

        # ---------------------------------------------------------
        # Tool registry
        # ---------------------------------------------------------
        self.tools = ToolRegistry()

        # Calculator
        self.tools.register(
            Tool(
                name="calculator",
                description=(
                    "Calculate basic arithmetic expressions."
                ),
                function=calculate,
            )
        )

        # Weather
        self.tools.register(
            Tool(
                name="weather",
                description=(
                    "Fetch current and forecast weather "
                    "for a location."
                ),
                function=get_weather,
            )
        )

        # ---------------------------------------------------------
        # Central tool router
        # ---------------------------------------------------------
        self.tool_router = ToolRouter(
            self.tools
        )

        # ---------------------------------------------------------
        # Short-term conversation history
        # ---------------------------------------------------------
        self.conversation: list[
            dict[str, str]
        ] = []

    # =============================================================
    # CONTEXT
    # =============================================================

    def get_current_context(self) -> str:
        """Return current date/time information."""

        now = datetime.now(
            ZoneInfo(self.TIMEZONE)
        )

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
            f"Current date: "
            f"{now.strftime('%d %B %Y')}\n"
            f"Current time: "
            f"{now.strftime('%I:%M %p')}\n"
            f"Day: "
            f"{now.strftime('%A')}\n"
            f"Time period: {period}\n"
            f"Timezone: {self.TIMEZONE}"
        )

    def get_goodbye(self) -> str:
        """Return a context-appropriate goodbye."""

        now = datetime.now(
            ZoneInfo(self.TIMEZONE)
        )

        hour = now.hour

        if 5 <= hour < 12:
            return "See you later, sir."

        if 12 <= hour < 17:
            return "See you later, sir."

        if 17 <= hour < 21:
            return "See you later, sir. Enjoy your evening."

        return "Goodnight, sir."

    # =============================================================
    # MEMORY
    # =============================================================

    def get_relevant_memory_text(
        self,
        query: str,
    ) -> str:
        """Retrieve memories relevant to the current request."""

        memories = get_relevant_memories(
            query
        )

        if not memories:
            return (
                "No relevant long-term memories "
                "were found."
            )

        lines = [
            "Relevant long-term memories:"
        ]

        for memory_type, content in memories:
            lines.append(
                f"- [{memory_type}] {content}"
            )

        return "\n".join(lines)

    def should_store_memory(
        self,
        user_message: str,
    ) -> bool:
        """
        Temporary memory detection.

        This will eventually be replaced by a proper
        memory extraction system.
        """

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
        """Ask before saving a possible personal memory."""

        print(
            "VYRA: That sounds like something that might "
            "be useful for me to remember. "
            "Should I save it? (yes/no)"
        )

        confirmation = input(
            "You: "
        ).strip().lower()

        if confirmation in {
            "yes",
            "y",
        }:
            save_memory(
                "user_note",
                user_message,
            )

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
        """Handle explicit /remember commands."""

        if not user_input.lower().startswith(
            "/remember "
        ):
            return False

        memory = user_input[
            len("/remember "):
        ].strip()

        if memory:
            save_memory(
                "user_note",
                memory,
            )

            print(
                "VYRA: Got it. I'll remember that.\n"
            )

        else:
            print(
                "VYRA: Tell me what you'd like "
                "me to remember.\n"
            )

        return True

    # =============================================================
    # TASKS
    # =============================================================

    def get_task_context(self) -> str:
        """Return pending tasks."""

        tasks = get_pending_tasks()

        if not tasks:
            return (
                "No pending tasks are currently stored."
            )

        lines = [
            "Pending tasks:"
        ]

        for task_id, title, due_at, status in tasks:
            due_text = (
                due_at
                if due_at
                else "No due time"
            )

            lines.append(
                f"- Task ID {task_id}: "
                f"{title} | Due: {due_text} | "
                f"Status: {status}"
            )

        return "\n".join(lines)

    def handle_task_command(
        self,
        user_input: str,
    ) -> bool:
        """
        Temporary developer command.

        Format:
        /task Task name | YYYY-MM-DD HH:MM
        """

        if not user_input.lower().startswith(
            "/task "
        ):
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

        title, due_at = task_data.split(
            "|",
            1,
        )

        title = title.strip()
        due_at = due_at.strip()

        if not title or not due_at:
            print(
                "VYRA: I need both the task "
                "and its due time.\n"
            )
            return True

        save_task(
            title,
            due_at,
        )

        print(
            f"VYRA: Got it. I'll remember the task "
            f"'{title}' for {due_at}.\n"
        )

        return True

    def extract_task_request(
        self,
        user_input: str,
    ) -> dict[str, str] | None:
        """
        Detect a basic natural-language reminder.

        This is an early deterministic prototype.
        """

        import re

        message = user_input.strip().lower()

        reminder_patterns = [
            r"\bremind me\b",
            r"\breminder\b",
            r"\bdon't let me forget\b",
            r"\bremember to\b",
        ]

        is_reminder = any(
            re.search(
                pattern,
                message,
            )
            for pattern in reminder_patterns
        )

        if not is_reminder:
            return None

        # ---------------------------------------------------------
        # Extract task text
        # ---------------------------------------------------------

        task_text = message

        task_text = re.sub(
            r"^\s*remind me\s+",
            "",
            task_text,
        )

        task_text = re.sub(
            r"^\s*a reminder\s+",
            "",
            task_text,
        )

        task_text = re.sub(
            r"^\s*to\s+",
            "",
            task_text,
        )

        task_text = re.sub(
            r"^(tomorrow|today)\s+",
            "",
            task_text,
        )

        task_text = re.sub(
            r"^at\s+\d{1,2}"
            r"(?::\d{2})?\s*(am|pm)?\s+",
            "",
            task_text,
        )

        task_text = re.sub(
            r"^(tomorrow|today)\s+at\s+"
            r"\d{1,2}(?::\d{2})?\s*"
            r"(am|pm)?\s+",
            "",
            task_text,
        )

        task_text = re.sub(
            r"^\s*to\s+",
            "",
            task_text,
        )

        task_text = task_text.rstrip(
            ".!? "
        )

        if not task_text:
            return None

        # ---------------------------------------------------------
        # Determine date/time
        # ---------------------------------------------------------

        now = datetime.now(
            ZoneInfo(self.TIMEZONE)
        )

        due_at: str | None = None

        if re.search(
            r"\btomorrow\b",
            message,
        ):
            target_date = (
                now.date().fromordinal(
                    now.date().toordinal() + 1
                )
            )

        elif re.search(
            r"\btoday\b",
            message,
        ):
            target_date = now.date()

        else:
            target_date = None

        time_match = re.search(
            r"\bat\s+"
            r"(\d{1,2})"
            r"(?::(\d{2}))?"
            r"\s*(am|pm)?",
            message,
        )

        if time_match and target_date:
            hour = int(
                time_match.group(1)
            )

            minute = int(
                time_match.group(2) or 0
            )

            meridiem = (
                time_match.group(3)
            )

            if (
                meridiem == "pm"
                and hour != 12
            ):
                hour += 12

            elif (
                meridiem == "am"
                and hour == 12
            ):
                hour = 0

            due_at = (
                f"{target_date.strftime('%Y-%m-%d')} "
                f"{hour:02d}:{minute:02d}"
            )

        return {
            "title": task_text,
            "due_at": due_at or "",
        }

    # =============================================================
    # TOOL SYSTEM
    # =============================================================

    def execute_tool_from_text(
        self,
        user_input: str,
    ) -> str | None:
        """
        Ask the central ToolRouter whether the user's
        message requires a tool.

        Returns the real tool result or None.
        """

        request = self.tool_router.detect(
            user_input
        )

        if request is None:
            return None

        return self.tool_router.execute(
            request
        )

    # =============================================================
    # BRAIN
    # =============================================================

    def generate_reply(
        self,
        user_input: str,
    ) -> str:
        """Generate a normal conversational response."""

        self.conversation.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        current_context = (
            self.get_current_context()
        )

        relevant_memory = (
            self.get_relevant_memory_text(
                user_input
            )
        )

        pending_tasks = (
            self.get_task_context()
        )

        model_request = f"""
CURRENT CONTEXT:
{current_context}

RELEVANT LONG-TERM MEMORY:
{relevant_memory}

CURRENT PENDING TASKS:
{pending_tasks}

CURRENT USER REQUEST:
{user_input}

Answer naturally.

Rules:
- Use relevant long-term memory when it directly helps.
- Use task information when it directly helps.
- Do not invent facts about Saksham.
- Do not mention unrelated memories or tasks.
- Do not claim that an action was performed unless it was actually performed.
- Do not claim that a reminder was delivered unless a reminder system
  actually delivered it.
"""

        messages_for_model: list[
            dict[str, str]
        ] = [
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

    # =============================================================
    # MAIN LOOP
    # =============================================================

    def run(self) -> None:
        """Start the VYRA text interface."""

        print("VYRA: Online.")
        print("Type 'exit' to close VYRA.")
        print("Commands:")
        print("  /remember <something>")
        print("  /task <task> | <YYYY-MM-DD HH:MM>")
        print()

        while True:
            user_input = input(
                "You: "
            ).strip()

            # -----------------------------------------------------
            # Exit
            # -----------------------------------------------------

            if user_input.lower() == "exit":
                print(
                    f"VYRA: {self.get_goodbye()}"
                )
                break

            if not user_input:
                continue

            # -----------------------------------------------------
            # Explicit memory command
            # -----------------------------------------------------

            if self.handle_remember_command(
                user_input
            ):
                continue

            # -----------------------------------------------------
            # Explicit developer task command
            # -----------------------------------------------------

            if self.handle_task_command(
                user_input
            ):
                continue

            # -----------------------------------------------------
            # Natural-language task detection
            # -----------------------------------------------------

            extracted_task = (
                self.extract_task_request(
                    user_input
                )
            )

            if extracted_task:
                title = extracted_task[
                    "title"
                ]

                due_at = extracted_task[
                    "due_at"
                ]

                if due_at:
                    print(
                        f"VYRA: I understood this "
                        f"as a reminder to "
                        f"'{title}' for {due_at}. "
                        f"Should I save it? (yes/no)"
                    )
                else:
                    print(
                        f"VYRA: I understood this "
                        f"as a task to "
                        f"'{title}'. "
                        f"Should I save it? (yes/no)"
                    )

                confirmation = input(
                    "You: "
                ).strip().lower()

                if confirmation in {
                    "yes",
                    "y",
                }:
                    save_task(
                        title,
                        due_at
                        if due_at
                        else None,
                    )

                    print(
                        "VYRA: Got it. "
                        "I've saved the task.\n"
                    )

                else:
                    print(
                        "VYRA: Okay, I won't "
                        "save it.\n"
                    )

                continue

            # -----------------------------------------------------
            # Central tool router
            # -----------------------------------------------------

            tool_result = (
                self.execute_tool_from_text(
                    user_input
                )
            )

            if tool_result is not None:
                print(
                    f"VYRA: {tool_result}\n"
                )
                continue

            # -----------------------------------------------------
            # Automatic memory detection
            # -----------------------------------------------------

            if self.should_store_memory(
                user_input
            ):
                self.save_memory_with_confirmation(
                    user_input
                )
                continue

            # -----------------------------------------------------
            # Normal conversation
            # -----------------------------------------------------

            reply = self.generate_reply(
                user_input
            )

            print(
                f"VYRA: {reply}\n"
            )