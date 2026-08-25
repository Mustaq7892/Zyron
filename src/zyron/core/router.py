from .agent import ZyronAgent
from .memory import ConversationMemory
from .tool_loader import register_core_tools
from .tool_registry import ToolRegistry


class ZyronRouter:
    """
    Central dynamic router for Zyron.

    Flow:

        User
          ↓
        Input Guard
          ↓
        Dynamic Agent
          ↓
        Ollama
          ↓
        Tool Registry
          ↓
        Capability
    """

    def __init__(
        self,
        memory=None,
        name="User",
    ):
        self.name = name

        # ====================================================
        # MEMORY
        # ====================================================

        self.memory = (
            memory
            if memory is not None
            else ConversationMemory()
        )

        # ====================================================
        # TOOL REGISTRY
        # ====================================================

        self.registry = ToolRegistry()

        register_core_tools(
            self.registry
        )

        # ====================================================
        # DYNAMIC AGENT
        # ====================================================

        self.agent = ZyronAgent(
            tool_registry=self.registry,
            memory=self.memory,
            name=self.name,
        )

    # ========================================================
    # GET TOOLS
    # ========================================================

    def get_tools(self):
        """
        Return all currently registered capabilities.
        """

        return self.registry.get_all()

    # ========================================================
    # GET TOOL NAMES
    # ========================================================

    def get_tool_names(self):
        """
        Return the names of all available capabilities.
        """

        return self.registry.get_names()

    # ========================================================
    # INPUT GUARD
    # ========================================================

    def _is_valid_input(self, command):
        """
        Perform lightweight input validation.

        This is NOT a command matcher.

        Its purpose is to prevent obvious application/UI
        artifacts or empty input from being sent to Ollama.

        Legitimate natural-language requests are allowed
        through dynamically.
        """

        if not isinstance(
            command,
            str,
        ):
            return False

        command = command.strip()

        if not command:
            return False

        # ----------------------------------------------------
        # Ignore Zyron's own console messages accidentally
        # being fed back as user input.
        # ----------------------------------------------------

        internal_prefixes = (
            "[Zyron is using tool:",
            "[Zyron is listening...]",
            "Zyron is now ON.",
            "Zyron is ready.",
            "Loading Faster-Whisper",
            "Faster-Whisper model loaded.",
            "Listening... Speak now.",
            "Calibrating microphone...",
            "Transcribing...",
        )

        for prefix in internal_prefixes:

            if command.startswith(prefix):
                return False

        # ----------------------------------------------------
        # Ignore obvious console prompts.
        # ----------------------------------------------------

        if command.startswith(
            "You:"
        ):
            return False

        if command.startswith(
            "Zyron:"
        ):
            return False

        return True

    # ========================================================
    # ROUTE
    # ========================================================

    def route(
        self,
        command,
        name=None,
        memory=None,
    ):
        """
        Send a user's request through the dynamic agent.

        Returns:

            response, should_exit
        """

        # ----------------------------------------------------
        # Validate input.
        # ----------------------------------------------------

        if not isinstance(
            command,
            str,
        ):
            return (
                "I didn't receive a valid command.",
                False,
            )

        command = command.strip()

        # ----------------------------------------------------
        # Empty input.
        # ----------------------------------------------------

        if not command:

            return (
                "I didn't hear a command.",
                False,
            )

        # ----------------------------------------------------
        # Ignore obvious internal console noise.
        # ----------------------------------------------------

        if not self._is_valid_input(
            command
        ):

            return (
                "",
                False,
            )

        # ====================================================
        # UPDATE NAME
        # ====================================================

        if name:

            self.name = name

            self.agent.name = name

        # ====================================================
        # UPDATE MEMORY
        # ====================================================

        if memory is not None:

            self.memory = memory

            self.agent.memory = memory

        # ====================================================
        # EXIT
        # ====================================================

        # Shutdown remains deterministic.
        # We don't ask the AI whether it should shut down.

        exit_commands = {
            "exit",
            "quit",
            "goodbye",
            "shutdown",
            "stop zyron",
            "turn off",
        }

        if command.lower() in exit_commands:

            return (
                "Goodbye!",
                True,
            )

        # ====================================================
        # DYNAMIC AGENT
        # ====================================================

        response = self.agent.process(
            command
        )

        return (
            response,
            False,
        )