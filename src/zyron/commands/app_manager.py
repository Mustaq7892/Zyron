import os
import shutil
import subprocess


# ============================================================
# ALLOWED APPLICATIONS
# ============================================================

APPLICATIONS = {
    "notepad": {
        "aliases": [
            "notepad",
            "note pad",
            "text editor",
        ],
        "command": ["notepad.exe"],
        "display_name": "Notepad",
    },

    "calculator": {
        "aliases": [
            "calculator",
            "calc",
        ],
        "command": ["calc.exe"],
        "display_name": "Calculator",
    },

    "paint": {
        "aliases": [
            "paint",
            "microsoft paint",
            "ms paint",
        ],
        "command": ["mspaint.exe"],
        "display_name": "Paint",
    },

    "chrome": {
        "aliases": [
            "chrome",
            "google chrome",
            "google browser",
            "chrome browser",
        ],
        "command": None,
        "display_name": "Google Chrome",
    },

    "vs_code": {
        "aliases": [
            "vs code",
            "visual studio code",
            "code",
        ],
        "command": None,
        "display_name": "Visual Studio Code",
    },
}


# ============================================================
# FIND APPLICATION
# ============================================================

def find_application(command):
    """
    Detect an allowed application from natural language.

    Returns the internal application name or None.
    """

    text = command.lower().strip()

    # Longest aliases first.
    aliases = []

    for application_name, information in APPLICATIONS.items():

        for alias in information["aliases"]:

            aliases.append(
                (alias, application_name)
            )

    aliases.sort(
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, application_name in aliases:

        if alias in text:
            return application_name

    return None


# ============================================================
# OPEN APPLICATION
# ============================================================

def open_application(application):
    """
    Open one of Zyron's explicitly allowed applications.
    """

    application = application.strip().lower()

    if application not in APPLICATIONS:

        return (
            f"I don't have permission to open "
            f"'{application}'. "
            "This application is not in my allowed "
            "application list."
        )

    information = APPLICATIONS[application]

    # --------------------------------------------------------
    # VS CODE
    # --------------------------------------------------------

    if application == "vs_code":

        code_path = shutil.which("code")

        if code_path:

            try:

                subprocess.Popen(
                    [code_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                return "Opening Visual Studio Code."

            except Exception as error:

                return (
                    "I couldn't open Visual Studio Code: "
                    f"{error}"
                )

        return (
            "Visual Studio Code is not available through "
            "the code command."
        )

    # --------------------------------------------------------
    # CHROME
    # --------------------------------------------------------

    if application == "chrome":

        chrome_paths = [

            os.path.expandvars(
                r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
            ),

            os.path.expandvars(
                r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
            ),

            os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
            ),
        ]

        for chrome_path in chrome_paths:

            if os.path.exists(chrome_path):

                try:

                    subprocess.Popen(
                        [chrome_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                    return "Opening Google Chrome."

                except Exception as error:

                    return (
                        "I couldn't open Google Chrome: "
                        f"{error}"
                    )

        # Chrome may be available through PATH.
        chrome_command = shutil.which("chrome")

        if chrome_command:

            try:

                subprocess.Popen(
                    [chrome_command],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                return "Opening Google Chrome."

            except Exception as error:

                return (
                    "I couldn't open Google Chrome: "
                    f"{error}"
                )

        return (
            "I couldn't find Google Chrome on this computer."
        )

    # --------------------------------------------------------
    # NORMAL WINDOWS APPLICATION
    # --------------------------------------------------------

    command = information["command"]

    try:

        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return (
            f"Opening {information['display_name']}."
        )

    except Exception as error:

        return (
            f"I couldn't open "
            f"{information['display_name']}: {error}"
        )


# ============================================================
# NATURAL LANGUAGE APPLICATION COMMAND
# ============================================================

def handle_application_command(command):
    """
    Detect whether the user wants to open an application.

    Examples:

        open chrome
        please open chrome
        can you launch chrome
        start google chrome
        open my browser
        launch notepad
        please start calculator
    """

    text = command.lower().strip()

    # --------------------------------------------------------
    # Determine whether this is actually an OPEN request.
    # --------------------------------------------------------

    action_words = (
        "open",
        "launch",
        "start",
        "run",
        "show",
    )

    has_open_action = any(
        word in text.split()
        for word in action_words
    )

    # Special natural-language phrases.
    special_open_phrases = (
        "my browser",
        "the browser",
        "web browser",
        "internet browser",
    )

    if not has_open_action and not any(
        phrase in text
        for phrase in special_open_phrases
    ):
        return None

    # --------------------------------------------------------
    # Browser aliases
    # --------------------------------------------------------

    if any(
        phrase in text
        for phrase in special_open_phrases
    ):

        if (
            "browser" in text
            and (
                "open" in text
                or "launch" in text
                or "start" in text
            )
        ):
            return open_application("chrome")

    # --------------------------------------------------------
    # Detect allowed application.
    # --------------------------------------------------------

    application = find_application(text)

    if application is None:
        return None

    return open_application(application)