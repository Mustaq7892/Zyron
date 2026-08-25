def handle_general_command(command, name):
    if command in ("hello", "hi", "hii"):
        return f"Hello {name}! How can I help you?", False

    if command == "help":
        return (
            "Available commands:\n"
            "- hello\n"
            "- hi\n"
            "- hii\n"
            "- help\n"
            "- exit\n"
            "- off"
        ), False

    if command == "exit":
        return "Goodbye!", True

    return None, False
