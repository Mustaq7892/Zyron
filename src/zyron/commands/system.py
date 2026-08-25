import os
import platform
import shutil
from datetime import datetime

import psutil


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_cpu_usage():
    """Return current CPU usage percentage."""
    cpu = psutil.cpu_percent(interval=0.5)
    return f"Current CPU usage is {cpu:.1f} percent."


def get_ram_usage():
    """Return current RAM usage information."""
    memory = psutil.virtual_memory()

    total_gb = memory.total / (1024 ** 3)
    used_gb = memory.used / (1024 ** 3)
    available_gb = memory.available / (1024 ** 3)
    percent = memory.percent

    return (
        "RAM Information:\n"
        f"Total RAM: {total_gb:.2f} GB\n"
        f"Used RAM: {used_gb:.2f} GB\n"
        f"Available RAM: {available_gb:.2f} GB\n"
        f"RAM Usage: {percent:.1f}%"
    )


def get_disk_usage():
    """Return C: drive disk usage."""
    try:
        disk = shutil.disk_usage("C:\\")

        total_gb = disk.total / (1024 ** 3)
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        percent = (disk.used / disk.total) * 100

        return (
            "C: Drive Information:\n"
            f"Total Space: {total_gb:.2f} GB\n"
            f"Used Space: {used_gb:.2f} GB\n"
            f"Free Space: {free_gb:.2f} GB\n"
            f"Disk Usage: {percent:.1f}%"
        )

    except Exception as error:
        return f"Unable to read disk information: {error}"


def get_battery_status():
    """Return battery information."""
    battery = psutil.sensors_battery()

    if battery is None:
        return "Battery information is not available."

    level = battery.percent

    if battery.power_plugged:
        power_status = "Plugged in"
    else:
        power_status = "Running on battery"

    return (
        "Battery Information:\n"
        f"Battery Level: {level:.1f}%\n"
        f"Power Status: {power_status}"
    )


def get_time():
    """Return current local time."""
    current_time = datetime.now().strftime("%I:%M:%S %p")
    return f"The current time is {current_time}."


def get_date():
    """Return current local date."""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return f"Today's date is {current_date}."


def get_computer_name():
    """Return computer name."""
    computer_name = platform.node()

    if not computer_name:
        return "I could not determine the computer name."

    return f"Your computer name is {computer_name}."


def get_system_status():
    """Return a complete system status report."""
    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()

    total_ram = memory.total / (1024 ** 3)
    used_ram = memory.used / (1024 ** 3)

    disk = shutil.disk_usage("C:\\")
    total_disk = disk.total / (1024 ** 3)
    free_disk = disk.free / (1024 ** 3)

    battery = psutil.sensors_battery()

    status = (
        "System Status:\n"
        f"CPU Usage: {cpu:.1f}%\n"
        f"RAM Usage: {memory.percent:.1f}% "
        f"({used_ram:.2f} / {total_ram:.2f} GB)\n"
        f"C: Drive Free Space: {free_disk:.2f} GB "
        f"of {total_disk:.2f} GB"
    )

    if battery is not None:
        status += f"\nBattery: {battery.percent:.1f}%"

        if battery.power_plugged:
            status += "\nPower: Plugged in"
        else:
            status += "\nPower: Running on battery"

    return status


# ============================================================
# COMMAND INTENT DETECTION
# ============================================================

def detect_system_intent(command):
    """
    Detect whether the user's command is asking for
    local system information.

    This intentionally uses concepts/keywords rather than
    exact full sentences.
    """

    text = command.lower().strip()

    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    cpu_words = (
        "cpu",
        "processor",
        "processing usage",
        "processor usage",
    )

    usage_words = (
        "usage",
        "using",
        "load",
        "percentage",
        "percent",
        "busy",
    )

    if any(word in text for word in cpu_words):
        if any(word in text for word in usage_words):
            return "cpu"

        # Questions such as:
        # "how is my processor"
        # "check my cpu"
        if any(word in text for word in (
            "check",
            "status",
            "how is",
            "how much",
            "tell me",
            "what is",
            "what's",
        )):
            return "cpu"

    # --------------------------------------------------------
    # RAM / MEMORY
    # --------------------------------------------------------

    ram_words = (
        "ram",
        "memory",
        "system memory",
    )

    if any(word in text for word in ram_words):

        if any(word in text for word in (
            "usage",
            "using",
            "used",
            "available",
            "free",
            "how much",
            "how many",
            "check",
            "status",
            "what is",
            "what's",
        )):
            return "ram"

    # --------------------------------------------------------
    # DISK / STORAGE
    # --------------------------------------------------------

    disk_words = (
        "disk",
        "storage",
        "drive",
        "hard disk",
        "hard drive",
        "space",
    )

    disk_question_words = (
        "space",
        "free",
        "available",
        "used",
        "usage",
        "capacity",
        "how much",
        "how many",
        "check",
        "status",
        "what is",
        "what's",
    )

    if any(word in text for word in disk_words):
        if any(word in text for word in disk_question_words):
            return "disk"

    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    battery_words = (
        "battery",
        "charge",
        "charging",
        "power level",
    )

    if any(word in text for word in battery_words):
        return "battery"

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    time_phrases = (
        "what time",
        "current time",
        "time is it",
        "tell me the time",
        "tell me time",
        "time right now",
        "what's the time",
        "what is the time",
    )

    if any(phrase in text for phrase in time_phrases):
        return "time"

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    date_phrases = (
        "what date",
        "today's date",
        "todays date",
        "current date",
        "what is today's date",
        "what is todays date",
        "what is today date",
        "what is todays date",
        "what is today",
        "what day is today",
    )

    if any(phrase in text for phrase in date_phrases):
        return "date"

    # --------------------------------------------------------
    # COMPUTER NAME
    # --------------------------------------------------------

    computer_name_phrases = (
        "computer name",
        "pc name",
        "device name",
        "machine name",
        "hostname",
        "host name",
    )

    if any(phrase in text for phrase in computer_name_phrases):
        return "computer_name"

    # --------------------------------------------------------
    # COMPLETE SYSTEM STATUS
    # --------------------------------------------------------

    system_phrases = (
        "system status",
        "system information",
        "system info",
        "computer status",
        "computer information",
        "pc status",
        "pc information",
        "show system",
        "check my system",
        "how is my system",
    )

    if any(phrase in text for phrase in system_phrases):
        return "system_status"

    return None


# ============================================================
# MAIN SYSTEM COMMAND HANDLER
# ============================================================

def handle_system_command(command):
    """
    Process natural-language system commands.

    Returns:
        response string if handled
        None if the command is not a system command
    """

    intent = detect_system_intent(command)

    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    if intent == "cpu":
        return get_cpu_usage()

    # --------------------------------------------------------
    # RAM
    # --------------------------------------------------------

    if intent == "ram":
        return get_ram_usage()

    # --------------------------------------------------------
    # DISK
    # --------------------------------------------------------

    if intent == "disk":
        return get_disk_usage()

    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    if intent == "battery":
        return get_battery_status()

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if intent == "time":
        return get_time()

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if intent == "date":
        return get_date()

    # --------------------------------------------------------
    # COMPUTER NAME
    # --------------------------------------------------------

    if intent == "computer_name":
        return get_computer_name()

    # --------------------------------------------------------
    # SYSTEM STATUS
    # --------------------------------------------------------

    if intent == "system_status":
        return get_system_status()

    # --------------------------------------------------------
    # NOT A SYSTEM COMMAND
    # --------------------------------------------------------

    return None