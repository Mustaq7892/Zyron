from .router import ZyronRouter


# ============================================================
# CREATE ROUTER ONCE
# ============================================================

router = ZyronRouter()


# ============================================================
# PROCESS COMMAND
# ============================================================

def process_command(command, name, memory):

    """
    Main entry point for Zyron commands.

    The command processor sends the user's command
    to the central Zyron router.
    """

    return router.route(
        command,
        name,
        memory,
    )