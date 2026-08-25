from src.zyron.core.router import ZyronRouter
from src.zyron.voice_input import listen
from src.zyron.voice import speak


# ============================================================
# ZYRON MAIN APPLICATION
# ============================================================


def print_header():
    print()
    print("================================")
    print("        ZYRON AI ASSISTANT")
    print("================================")
    print()


def activate_zyron():
    """
    Deterministic activation.
    """

    while True:

        command = input(
            "Zyron [OFF]: "
        ).strip()

        if command.lower() in {
            "on",
            "activate",
            "start",
            "start zyron",
            "turn on",
        }:

            print()
            print(
                "Zyron is now ON."
            )

            print(
                "Zyron is ready."
            )

            return True

        if command.lower() in {
            "exit",
            "quit",
        }:

            return False

        print(
            "Type ON to activate Zyron "
            "or EXIT to close."
        )


def choose_input_mode():
    """
    Let the user choose text or voice input.
    """

    print()

    print(
        "Choose input mode:"
    )

    print(
        "1. Text"
    )

    print(
        "2. Voice"
    )

    print()

    while True:

        choice = input(
            "Select mode [1/2]: "
        ).strip()

        if choice == "1":

            return "text"

        if choice == "2":

            return "voice"

        print(
            "Please select 1 or 2."
        )


def run_text_mode(router):
    """
    Dynamic text interface.

    Text mode prints Zyron's response.
    """

    print()

    print(
        "Text mode activated."
    )

    print(
        "You can type commands."
    )

    print()

    while True:

        try:

            command = input(
                "You: "
            ).strip()

        except (
            EOFError,
            KeyboardInterrupt,
        ):

            print()

            print(
                "Goodbye!"
            )

            break

        if not command:

            continue

        response, should_exit = router.route(
            command,
            router.name,
        )

        if response:

            print(
                f"Zyron: {response}"
            )

        if should_exit:

            break


def run_voice_mode(router):
    """
    Dynamic voice interface.

    Pipeline:

        Microphone
             ↓
        Faster-Whisper
             ↓
        Text command
             ↓
        ZyronRouter
             ↓
        Dynamic Agent
             ↓
        ToolRegistry
             ↓
        Response
             ↓
        Piper TTS
             ↓
        Speaker
    """

    print()

    print(
        "Voice mode activated."
    )

    print(
        "Speak your commands."
    )

    print()

    while True:

        print(
            "[Zyron is listening...]"
        )

        # ----------------------------------------------------
        # Capture and validate speech.
        # ----------------------------------------------------

        command = listen()

        # ----------------------------------------------------
        # No valid speech.
        #
        # Do NOT send empty/rejected audio to the agent.
        # ----------------------------------------------------

        if not command:

            continue

        # ----------------------------------------------------
        # Route the validated natural-language command.
        # ----------------------------------------------------

        response, should_exit = router.route(
            command,
            router.name,
        )

        # ----------------------------------------------------
        # Display Zyron's response.
        # ----------------------------------------------------

        if response:

            print()

            print(
                f"Zyron: {response}"
            )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # Send the response to Piper TTS.
            # This is what makes Zyron speak through
            # the computer speakers.
            # ------------------------------------------------

            speak(response)

        # ----------------------------------------------------
        # Shutdown.
        # ----------------------------------------------------

        if should_exit:

            break


def main():

    print_header()

    # --------------------------------------------------------
    # Activation
    # --------------------------------------------------------

    activated = activate_zyron()

    if not activated:

        print(
            "Zyron is shutting down."
        )

        return

    # --------------------------------------------------------
    # User name
    # --------------------------------------------------------

    print()

    name = input(
        "What is your name? "
    ).strip()

    if not name:

        name = "User"

    print()

    print(
        f"Hello. I am Zyron, your personal "
        f"AI assistant. How can I help you, "
        f"{name}?"
    )

    # --------------------------------------------------------
    # Create the central dynamic router.
    # --------------------------------------------------------

    router = ZyronRouter(
        name=name
    )

    # --------------------------------------------------------
    # Display currently registered capabilities.
    # --------------------------------------------------------

    print()

    print(
        "Zyron currently has these capabilities:"
    )

    for tool_name in router.get_tool_names():

        print(
            f"  - {tool_name}"
        )

    # --------------------------------------------------------
    # Input mode.
    # --------------------------------------------------------

    mode = choose_input_mode()

    # --------------------------------------------------------
    # Run selected interface.
    # --------------------------------------------------------

    if mode == "text":

        run_text_mode(
            router
        )

    elif mode == "voice":

        run_voice_mode(
            router
        )

    print()

    print(
        "Zyron has been shut down."
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()