from .tool_registry import ToolRegistry

from ..ai.ollama_client import ask_ollama

from ..commands.system import handle_system_command

from ..commands.app_manager import (
    handle_application_command,
)

from ..commands.file_manager import (
    open_zyron_folder,
    list_zyron_files,
    create_folder,
    create_file,
    write_file,
    open_file,
    read_file,
    delete_item,
    rename_item,
)

from ..commands.web_search import (
    search_web,
)


# ============================================================
# SYSTEM TOOL
# ============================================================

def system_tool(
    query: str,
):
    """
    Dynamic system-information capability.

    Fast path:
        Recognize common natural-language system requests
        locally before using Ollama.

    Examples:

        "What is my CPU usage?"
        "How hard is my processor working?"
        "How busy is my processor?"
        "How much RAM am I using?"
        "How much memory am I using?"

    If the request cannot be safely recognized locally,
    Ollama remains available as the fallback interpreter.
    """

    query = str(
        query
    ).strip()

    if not query:
        return (
            "I need to know what system information "
            "you want me to check."
        )

    # ========================================================
    # FIRST: EXISTING DIRECT SYSTEM HANDLER
    # ========================================================

    direct_result = handle_system_command(
        query
    )

    if direct_result is not None:
        return direct_result

    # ========================================================
    # FAST LOCAL SYSTEM-INTENT NORMALIZATION
    # ========================================================

    text = query.lower().strip()

    # --------------------------------------------------------
    # CPU / PROCESSOR
    # --------------------------------------------------------

    cpu_indicators = (
        "cpu",
        "processor",
        "processing",
        "processor working",
        "processor usage",
        "processor load",
        "cpu usage",
        "cpu load",
        "cpu utilization",
        "processor utilization",
        "processor workload",
        "how hard is my processor",
        "how busy is my processor",
        "how much is my processor working",
        "how hard is my cpu",
        "how busy is my cpu",
        "how much is my cpu working",
    )

    cpu_question_indicators = (
        "how hard",
        "how busy",
        "how much",
        "usage",
        "utilization",
        "load",
        "working",
        "workload",
        "busy",
    )

    if (
        any(
            indicator in text
            for indicator in cpu_indicators
        )
        and any(
            indicator in text
            for indicator in cpu_question_indicators
        )
    ):
        result = handle_system_command(
            "what is my cpu usage"
        )

        if result is not None:
            return result

    # --------------------------------------------------------
    # RAM / MEMORY
    # --------------------------------------------------------

    memory_indicators = (
        "ram",
        "memory",
        "ram usage",
        "memory usage",
        "memory utilization",
        "memory load",
        "how much ram",
        "how much memory",
        "ram am i using",
        "memory am i using",
        "ram is being used",
        "memory is being used",
    )

    memory_question_indicators = (
        "usage",
        "utilization",
        "load",
        "using",
        "used",
        "how much",
        "how many",
    )

    if (
        any(
            indicator in text
            for indicator in memory_indicators
        )
        and any(
            indicator in text
            for indicator in memory_question_indicators
        )
    ):
        result = handle_system_command(
            "what is my ram usage"
        )

        if result is not None:
            return result

    # --------------------------------------------------------
    # DISK SPACE
    # --------------------------------------------------------

    disk_indicators = (
        "disk space",
        "storage space",
        "free disk",
        "free storage",
        "hard drive space",
        "hard disk space",
        "drive space",
        "disk usage",
        "storage usage",
    )

    if any(
        indicator in text
        for indicator in disk_indicators
    ):
        result = handle_system_command(
            "how much disk space do i have"
        )

        if result is not None:
            return result

    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    battery_indicators = (
        "battery",
        "battery status",
        "battery level",
        "battery percentage",
        "how much battery",
        "how much charge",
        "power remaining",
    )

    if any(
        indicator in text
        for indicator in battery_indicators
    ):
        result = handle_system_command(
            "what is my battery status"
        )

        if result is not None:
            return result

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    time_indicators = (
        "what time is it",
        "current time",
        "time right now",
        "time now",
        "tell me the time",
    )

    if any(
        indicator in text
        for indicator in time_indicators
    ):
        result = handle_system_command(
            "what is the time"
        )

        if result is not None:
            return result

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    date_indicators = (
        "today's date",
        "todays date",
        "what is the date",
        "what's the date",
        "current date",
        "date today",
        "today date",
    )

    if any(
        indicator in text
        for indicator in date_indicators
    ):
        result = handle_system_command(
            "what is today's date"
        )

        if result is not None:
            return result

    # --------------------------------------------------------
    # COMPUTER NAME
    # --------------------------------------------------------

    computer_name_indicators = (
        "computer name",
        "computer's name",
        "pc name",
        "machine name",
        "hostname",
        "host name",
    )

    if any(
        indicator in text
        for indicator in computer_name_indicators
    ):
        result = handle_system_command(
            "what is my computer name"
        )

        if result is not None:
            return result

    # --------------------------------------------------------
    # SYSTEM STATUS
    # --------------------------------------------------------

    system_status_indicators = (
        "system status",
        "computer status",
        "pc status",
        "system information",
        "computer information",
        "system details",
        "computer details",
    )

    if any(
        indicator in text
        for indicator in system_status_indicators
    ):
        result = handle_system_command(
            "show my system status"
        )

        if result is not None:
            return result

    # ========================================================
    # OLLAMA FALLBACK
    # ========================================================

    prompt = f"""
        You are a system-command interpreter for Zyron.

        Convert the user's natural-language request into ONE
        canonical system request.

        User request:

        {query}

        Choose ONLY ONE of these canonical requests:

        - what is my cpu usage
        - what is my ram usage
        - how much disk space do i have
        - what is my battery status
        - what is the time
        - what is today's date
        - what is my computer name
        - show my system status

        Return ONLY the canonical request.

        Do not explain anything.

        Do not use quotes.

        Do not add punctuation.
    """

    try:
        interpreted_query = ask_ollama(
            prompt
        ).strip()

    except Exception:
        return (
            "I couldn't interpret that system request."
        )

    # --------------------------------------------------------
    # Clean model formatting
    # --------------------------------------------------------

    interpreted_query = (
        interpreted_query
        .strip()
        .strip('"')
        .strip("'")
        .strip()
    )

    # --------------------------------------------------------
    # SECURITY / VALIDATION
    # --------------------------------------------------------

    allowed_requests = {
        "what is my cpu usage",
        "what is my ram usage",
        "how much disk space do i have",
        "what is my battery status",
        "what is the time",
        "what is today's date",
        "what is my computer name",
        "show my system status",
    }

    if (
        interpreted_query.lower()
        not in allowed_requests
    ):
        return (
            "I couldn't determine which supported "
            "system information you requested."
        )

    # --------------------------------------------------------
    # Execute only a known canonical request
    # --------------------------------------------------------

    result = handle_system_command(
        interpreted_query
    )

    if result is None:
        return (
            "The system capability could not retrieve "
            "that information."
        )

    return result


# ============================================================
# APPLICATION TOOL
# ============================================================

def application_tool(
    command: str,
):
    """
    Dynamic desktop application capability.
    """

    command = str(command).strip()

    if not command:
        return (
            "I need to know which application "
            "you want me to open."
        )

    return handle_application_command(
        command
    )


# ============================================================
# OPEN ZYRON FOLDER
# ============================================================

def open_zyron_folder_tool():
    """
    Open the Zyron project folder.
    """

    return open_zyron_folder()


# ============================================================
# LIST ZYRON FILES
# ============================================================

def list_zyron_files_tool():
    """
    List files and folders inside the Zyron project.

    This capability should handle natural-language requests
    such as:

        "List the files in my Zyron folder."
        "Show me the files in my Zyron folder."
        "What is inside my Zyron folder?"
        "What's in my Zyron folder?"
        "Show me what is in the Zyron folder."
        "Show me what's inside the Zyron folder."
        "Display the contents of my Zyron folder."
        "What's inside the Zyron project?"
    """

    return list_zyron_files()


# ============================================================
# CREATE FOLDER
# ============================================================

def create_folder_tool(
    folder_name: str,
):
    """
    Create a folder inside the Zyron workspace.
    """

    folder_name = str(
        folder_name
    ).strip()

    if not folder_name:
        return (
            "I need a folder name."
        )

    return create_folder(
        folder_name
    )


# ============================================================
# CREATE FILE
# ============================================================

def create_file_tool(
    file_name: str,
):
    """
    Create a new file inside the Zyron workspace.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:
        return (
            "I need a file name."
        )

    return create_file(
        file_name
    )

# ============================================================
# WRITE FILE
# ============================================================

def write_file_tool(
    file_name: str,
    content: str,
):
    """
    Write content into an existing file inside
    the Zyron workspace.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:
        return (
            "I need a file name."
        )

    return write_file(
        file_name,
        content,
    )


# ============================================================
# OPEN FILE
# ============================================================

def open_file_tool(
    file_name: str,
):
    """
    Open a file from the Zyron workspace.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:
        return (
            "I need a file name."
        )

    return open_file(
        file_name
    )


# ============================================================
# READ FILE
# ============================================================

def read_file_tool(
    file_name: str,
):
    """
    Read the contents of a text or code file
    from the Zyron workspace.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:
        return (
            "I need a file name."
        )

    return read_file(
        file_name
    )

def delete_item_tool(
    item_name: str,
):
    """
    Delete a file or folder from the Zyron workspace.
    """

    item_name = str(
        item_name
    ).strip()

    if not item_name:
        return (
            "I need a file or folder name."
        )

    return delete_item(
        item_name
    )


# ============================================================
# RENAME FILE OR FOLDER
# ============================================================

def rename_item_tool(
    item_name: str,
    new_name: str,
):
    """
    Rename a file or folder inside the Zyron workspace.
    """

    item_name = str(
        item_name
    ).strip()

    new_name = str(
        new_name
    ).strip()

    if not item_name:

        return (
            "I need the file or folder name "
            "you want to rename."
        )

    if not new_name:

        return (
            "I need the new file or folder name."
        )

    return rename_item(
        item_name,
        new_name,
    )


# ============================================================
# WEB SEARCH
# ============================================================

def web_search_tool(
    query: str,
):
    """
    Dynamic web-search capability.
    """

    query = str(
        query
    ).strip()

    if not query:
        return (
            "I need something to search for."
        )

    return search_web(
        query,
        5,
    )


# ============================================================
# CALCULATOR TOOL
# ============================================================

def calculate_scaled_value_tool(
    value: int,
    multiplier: int,
):
    """
    Multiply one numeric value by another numeric value.

    Both arguments are required and must come from the user's
    request. The planner/agent validation layer is responsible
    for preventing invented numeric arguments.
    """

    return (
        f"Calculated result: "
        f"{value * multiplier}"
    )


# ============================================================
# REGISTER CORE TOOLS
# ============================================================

def register_core_tools(
    registry: ToolRegistry,
):
    """
    Register Zyron's core capabilities.
    """

    # --------------------------------------------------------
    # CALCULATOR
    # --------------------------------------------------------

    registry.register(
        name="calculate_scaled_value",
        description=(
            "Calculate a numeric value multiplied by another "
            "numeric value. Use this when the user asks to "
            "calculate, multiply, or find the product of two "
            "numbers. Required arguments: value and multiplier."
        ),
        function=calculate_scaled_value_tool,
    )


    # --------------------------------------------------------
    # SYSTEM
    # --------------------------------------------------------

    registry.register(
        name="system",
        description=(
            "Get real-time information about the user's "
            "computer. Use this for CPU usage, processor "
            "usage, RAM usage, memory usage, disk space, "
            "battery status, power status, current time, "
            "today's date, computer name, and overall "
            "system status. "
            "Required argument: query."
        ),
        function=system_tool,
    )

    # --------------------------------------------------------
    # APPLICATION
    # --------------------------------------------------------

    registry.register(
        name="application",
        description=(
            "Open or launch a desktop application. "
            "Use this whenever the user's intent is to "
            "start or open an application. The user can "
            "describe the request naturally. Examples "
            "include opening a browser, launching Chrome, "
            "starting Notepad, opening Calculator, "
            "launching Paint, or opening Visual Studio "
            "Code. Required argument: command."
        ),
        function=application_tool,
    )

    # --------------------------------------------------------
    # ZYRON FOLDER
    # --------------------------------------------------------

    registry.register(
        name="open_zyron_folder",
        description=(
            "Open the user's Zyron project folder."
        ),
        function=open_zyron_folder_tool,
    )

    # --------------------------------------------------------
    # LIST FILES
    # --------------------------------------------------------

    registry.register(
        name="list_zyron_files",
        description=(
            "List, show, display, inspect, or view the "
            "files, folders, and contents inside the user's "
            "Zyron project folder. Use this when the user "
            "asks what is inside the Zyron folder, what is "
            "in the Zyron folder, what the Zyron folder "
            "contains, or asks to see or list its contents. "
            "Examples: 'List the files in my Zyron folder', "
            "'Show me the files in my Zyron folder', "
            "'What is inside my Zyron folder?', "
            "'What's in the Zyron folder?', "
            "'Show me what is in the Zyron folder', "
            "'Display the contents of my Zyron folder'."
        ),
        function=list_zyron_files_tool,
    )

    # --------------------------------------------------------
    # CREATE FOLDER
    # --------------------------------------------------------

    registry.register(
        name="create_folder",
        description=(
            "Create a new folder inside the Zyron "
            "workspace. Use this when the user explicitly "
            "asks to create, make, or add a new folder. "
            "Required argument: folder_name."
        ),
        function=create_folder_tool,
    )


    # --------------------------------------------------------
    # CREATE FILE
    # --------------------------------------------------------

    registry.register(
        name="create_file",
        description=(
            "Create a new file inside the Zyron workspace. "
            "Use this when the user explicitly asks to create "
            "or make a new file. "
            "Required argument: file_name."
        ),
        function=create_file_tool,
        parameters={
            "file_name": {
                "type": "string",
                "required": True,
            }
        },
    )


    # --------------------------------------------------------
    # WRITE FILE
    # --------------------------------------------------------

    registry.register(
        name="write_file",
        description=(
            "Write text content into an existing file "
            "inside the Zyron workspace. "
            "Use this when the user explicitly asks to "
            "write, add, or replace content in a file. "
            "This modifies an existing file and requires "
            "user confirmation before execution. "
            "Required arguments: file_name and content."
        ),
        function=write_file_tool,
        parameters={
            "file_name": {
                "type": "string",
                "required": True,
            },
            "content": {
                "type": "string",
                "required": True,
            },
        },
        requires_confirmation=True,
    )

    # --------------------------------------------------------
    # OPEN FILE
    # --------------------------------------------------------

    registry.register(
        name="open_file",
        description=(
            "Open a file from the Zyron workspace. "
            "Required argument: file_name."
        ),
        function=open_file_tool,
    )


    # ============================================================
    # READ FILE
    # ============================================================

    registry.register(
    name="read_file",
    description=(
        "Read and display the contents of a text or code file "
        "inside the user's Zyron project folder. "
        "Use this when the user asks to read, show, display, "
        "inspect, view, or see the contents of a specific file. "
        "Required argument: file_name."
    ),
    function=read_file_tool,
    parameters={
        "file_name": {
            "type": "string",
            "required": True,
        }
    },
    )


    # ========================================================
    # DELETE FILE OR FOLDER
    # ========================================================

    registry.register(
        name="delete_item",
        description=(
            "Delete a file or folder inside the user's Zyron "
            "project folder. Use this when the user explicitly "
            "asks to delete, remove, or erase a specific file "
            "or folder. Required argument: item_name."
        ),
        function=delete_item_tool,
        parameters={
            "item_name": {
                "type": "string",
                "required": True,
            }
        },
        requires_confirmation=True,
    )

    # ============================================================
    # RENAME FILE OR FOLDER
    # ============================================================

    registry.register(
        name="rename_item",
        description=(
            "Rename a file or folder inside the user's Zyron "
            "project folder. Use this when the user explicitly "
            "asks to rename or change the name of a specific "
            "file or folder. Required arguments: item_name "
            "and new_name."
        ),
        function=rename_item_tool,
        parameters={
            "item_name": {
                "type": "string",
                "required": True,
            },
            "new_name": {
                "type": "string",
                "required": True,
            },
        },
        requires_confirmation=True,
    )

    # --------------------------------------------------------
    # WEB SEARCH
    # --------------------------------------------------------

    registry.register(
        name="web_search",
        description=(
            "Search the internet for information. "
            "Use this when the user explicitly asks "
            "for an internet search or current online "
            "information. Required argument: query."
        ),
        function=web_search_tool,
    )

    return registry