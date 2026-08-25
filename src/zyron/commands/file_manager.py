from pathlib import Path

import os


# ============================================================
# ZYRON PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ============================================================
# OPEN ZYRON FOLDER
# ============================================================

def open_zyron_folder():
    """
    Open the Zyron project folder in Windows Explorer.
    """

    try:
        os.startfile(PROJECT_ROOT)

        return "Opening the Zyron folder."

    except Exception as error:

        return (
            f"I couldn't open the Zyron folder: "
            f"{error}"
        )


# ============================================================
# LIST ZYRON FILES
# ============================================================

def list_zyron_files():
    """
    Return files and folders in the Zyron project folder.
    """

    try:

        items = sorted(
            PROJECT_ROOT.iterdir(),
            key=lambda item: (
                not item.is_dir(),
                item.name.lower(),
            ),
        )

        if not items:

            return "The Zyron folder is empty."

        lines = [
            "Here are the items in the Zyron folder:"
        ]

        for item in items:

            if item.is_dir():

                lines.append(
                    f"[Folder] {item.name}"
                )

            else:

                lines.append(
                    f"[File] {item.name}"
                )

        return "\n".join(lines)

    except Exception as error:

        return (
            f"I couldn't list the Zyron folder: "
            f"{error}"
        )


# ============================================================
# CREATE FOLDER
# ============================================================

def create_folder(folder_name):
    """
    Create a folder inside the Zyron project folder.
    """

    folder_name = str(
        folder_name
    ).strip()

    if not folder_name:

        return "Please provide a folder name."

    target = (
        PROJECT_ROOT / folder_name
    ).resolve()

    # --------------------------------------------------------
    # Prevent escaping the Zyron project directory.
    # --------------------------------------------------------

    if PROJECT_ROOT not in target.parents:

        return (
            "I can only create folders "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Check whether it already exists.
    # --------------------------------------------------------

    if target.exists():

        return (
            f"The folder '{folder_name}' "
            "already exists."
        )

    # --------------------------------------------------------
    # Create folder.
    # --------------------------------------------------------

    try:

        target.mkdir(
            parents=False
        )

        return (
            f"Created the folder "
            f"'{folder_name}'."
        )

    except Exception as error:

        return (
            f"I couldn't create that folder: "
            f"{error}"
        )


# ============================================================
# OPEN FILE
# ============================================================

def open_file(file_name):
    """
    Open a file that exists inside the Zyron project folder.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:

        return "Please provide a file name."

    target = (
        PROJECT_ROOT / file_name
    ).resolve()

    # --------------------------------------------------------
    # Prevent access outside the Zyron project directory.
    # --------------------------------------------------------

    if PROJECT_ROOT not in target.parents:

        return (
            "I can only open files "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Check existence.
    # --------------------------------------------------------

    if not target.exists():

        return (
            f"I couldn't find '{file_name}' "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Make sure it is actually a file.
    # --------------------------------------------------------

    if not target.is_file():

        return (
            f"'{file_name}' is not a file."
        )

    # --------------------------------------------------------
    # Open file.
    # --------------------------------------------------------

    try:

        os.startfile(target)

        return (
            f"Opening {file_name}."
        )

    except Exception as error:

        return (
            f"I couldn't open {file_name}: "
            f"{error}"
        )


# ============================================================
# READ FILE
# ============================================================

def read_file(file_name):
    """
    Read and display the contents of a text or code file
    inside the Zyron project folder.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:

        return "Please provide a file name."

    target = (
        PROJECT_ROOT / file_name
    ).resolve()

    # --------------------------------------------------------
    # Prevent access outside the Zyron project directory.
    # --------------------------------------------------------

    if PROJECT_ROOT not in target.parents:

        return (
            "I can only read files "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Check existence.
    # --------------------------------------------------------

    if not target.exists():

        return (
            f"I couldn't find '{file_name}' "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Make sure it is actually a file.
    # --------------------------------------------------------

    if not target.is_file():

        return (
            f"'{file_name}' is not a file."
        )

    # --------------------------------------------------------
    # Read file.
    # --------------------------------------------------------

    try:

        content = target.read_text(
            encoding="utf-8"
        )

        return (
            f"Contents of '{file_name}':\n\n"
            f"{content}"
        )

    except UnicodeDecodeError:

        return (
            f"I couldn't read '{file_name}' "
            "because it is not a UTF-8 text file."
        )

    except Exception as error:

        return (
            f"I couldn't read '{file_name}': "
            f"{error}"
        )


# ============================================================
# WINDOWS DELETE ERROR HANDLER
# ============================================================

def _handle_delete_error(
    function,
    path,
    exc_info,
):
    """
    Handle filesystem errors while deleting files/folders.

    Windows can sometimes mark a file as read-only.
    In that case, make it writable and retry the operation.
    """

    import os
    import stat

    try:

        os.chmod(
            path,
            stat.S_IWRITE,
        )

        function(
            path
        )

    except Exception:

        raise


# ============================================================
# DELETE FILE OR FOLDER
# ============================================================

def delete_item(item_name):
    """
    Safely delete a file or folder inside the Zyron
    project folder.

    Safety rules:

    - Only items inside the Zyron project folder can be deleted.
    - The Zyron project root itself can never be deleted.
    - The item must already exist.
    - Directory deletion uses shutil.rmtree().
    - Read-only filesystem errors are handled automatically.
    """

    item_name = str(
        item_name
    ).strip()

    if not item_name:

        return (
            "Please provide a file or folder name."
        )

    target = (
        PROJECT_ROOT / item_name
    ).resolve()

    # --------------------------------------------------------
    # SAFETY CHECK #1
    #
    # Prevent paths such as:
    #
    # ..\Desktop
    # ..\Documents
    # C:\Users\...
    #
    # from escaping the Zyron directory.
    # --------------------------------------------------------

    if PROJECT_ROOT not in target.parents:

        return (
            "I can only delete files or folders "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # SAFETY CHECK #2
    #
    # Never allow the Zyron project root itself to be deleted.
    # --------------------------------------------------------

    if target == PROJECT_ROOT:

        return (
            "I cannot delete the Zyron project folder."
        )

    # --------------------------------------------------------
    # Check whether the requested item exists.
    # --------------------------------------------------------

    if not target.exists():

        return (
            f"I couldn't find '{item_name}' "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Remember whether this is a directory.
    #
    # We need this BEFORE deletion because after deletion
    # target.exists() will be False.
    # --------------------------------------------------------

    was_directory = target.is_dir()

    # --------------------------------------------------------
    # Perform deletion.
    # --------------------------------------------------------

    try:

        if was_directory:

            import shutil

            shutil.rmtree(
                target,
                onerror=_handle_delete_error,
            )

        else:

            try:

                target.unlink()

            except PermissionError:

                # ------------------------------------------------
                # Windows may mark a file read-only.
                # Make it writable and retry.
                # ------------------------------------------------

                import stat

                os.chmod(
                    target,
                    stat.S_IWRITE,
                )

                target.unlink()

        # --------------------------------------------------------
        # Confirm deletion.
        # --------------------------------------------------------

        if target.exists():

            return (
                f"I couldn't confirm deletion "
                f"of '{item_name}'."
            )

        # --------------------------------------------------------
        # Return appropriate result.
        # --------------------------------------------------------

        if was_directory:

            return (
                f"Deleted the folder "
                f"'{item_name}'."
            )

        return (
            f"Deleted the file "
            f"'{item_name}'."
        )

    except Exception as error:

        return (
            f"I couldn't delete "
            f"'{item_name}': {error}"
        )


# ============================================================
# CREATE FILE
# ============================================================

def create_file(file_name):
    """
    Create a new empty file inside the Zyron project folder.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:

        return (
            "Please provide a file name."
        )

    target = (
        PROJECT_ROOT / file_name
    ).resolve()

    # --------------------------------------------------------
    # Prevent escaping the Zyron project directory.
    # --------------------------------------------------------

    if PROJECT_ROOT not in target.parents:

        return (
            "I can only create files "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Check whether the file already exists.
    # --------------------------------------------------------

    if target.exists():

        return (
            f"The item '{file_name}' "
            "already exists."
        )

    # --------------------------------------------------------
    # Make sure the parent directory exists.
    # --------------------------------------------------------

    parent = target.parent

    if not parent.exists():

        return (
            f"The parent folder for '{file_name}' "
            "does not exist."
        )

    # --------------------------------------------------------
    # Create the empty file.
    # --------------------------------------------------------

    try:

        target.touch(
            exist_ok=False
        )

        return (
            f"Created the file "
            f"'{file_name}'."
        )

    except Exception as error:

        return (
            f"I couldn't create "
            f"'{file_name}': {error}"
        )

# ============================================================
# WRITE FILE
# ============================================================

def write_file(
    file_name,
    content,
):
    """
    Write text content into an existing file inside
    the Zyron project folder.

    Existing files are protected by default.
    Overwriting requires explicit permission through
    the overwrite parameter.
    """

    file_name = str(
        file_name
    ).strip()

    if not file_name:

        return (
            "Please provide a file name."
        )

    target = (
        PROJECT_ROOT / file_name
    ).resolve()

    # --------------------------------------------------------
    # Prevent escaping the Zyron project directory.
    # --------------------------------------------------------

    if PROJECT_ROOT not in target.parents:

        return (
            "I can only write files "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # The target must already exist.
    # --------------------------------------------------------

    if not target.exists():

        return (
            f"The file '{file_name}' "
            "does not exist."
        )

    # --------------------------------------------------------
    # Do not write into a directory.
    # --------------------------------------------------------

    if not target.is_file():

        return (
            f"'{file_name}' is not a file."
        )

    # --------------------------------------------------------
    # Write the content.
    # --------------------------------------------------------

    try:

        target.write_text(
            str(content),
            encoding="utf-8",
        )

        return (
            f"Successfully wrote content "
            f"to '{file_name}'."
        )

    except Exception as error:

        return (
            f"I couldn't write to "
            f"'{file_name}': {error}"
        )

# ============================================================
# RENAME FILE OR FOLDER
# ============================================================

def rename_item(
    item_name,
    new_name,
):
    """
    Rename a file or folder inside the Zyron
    project folder.

    Safety rules:

    - Only items inside the Zyron project folder can be renamed.
    - The Zyron project root itself can never be renamed.
    - The original item must already exist.
    - The destination must not already exist.
    - The destination must remain inside the Zyron project folder.
    """

    item_name = str(
        item_name
    ).strip()

    new_name = str(
        new_name
    ).strip()

    if not item_name:

        return (
            "Please provide the file or folder "
            "name to rename."
        )

    if not new_name:

        return (
            "Please provide the new file or folder "
            "name."
        )

    # --------------------------------------------------------
    # Resolve original item.
    # --------------------------------------------------------

    source = (
        PROJECT_ROOT / item_name
    ).resolve()

    # --------------------------------------------------------
    # SAFETY CHECK #1
    # Prevent escaping the Zyron directory.
    # --------------------------------------------------------

    if PROJECT_ROOT not in source.parents:

        return (
            "I can only rename files or folders "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # SAFETY CHECK #2
    # Never rename the Zyron project root itself.
    # --------------------------------------------------------

    if source == PROJECT_ROOT:

        return (
            "I cannot rename the Zyron project folder."
        )

    # --------------------------------------------------------
    # Check whether the original item exists.
    # --------------------------------------------------------

    if not source.exists():

        return (
            f"I couldn't find '{item_name}' "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # Build destination.
    #
    # If the user gives only a new name, keep the item
    # in its current parent folder.
    # --------------------------------------------------------

    destination = (
        source.parent / new_name
    ).resolve()

    # --------------------------------------------------------
    # SAFETY CHECK #3
    # Destination must remain inside Zyron.
    # --------------------------------------------------------

    if PROJECT_ROOT not in destination.parents:

        return (
            "I can only rename files or folders "
            "inside the Zyron folder."
        )

    # --------------------------------------------------------
    # SAFETY CHECK #4
    # Destination must not already exist.
    # --------------------------------------------------------

    if destination.exists():

        return (
            f"The item '{new_name}' "
            "already exists."
        )

    # --------------------------------------------------------
    # Perform rename.
    # --------------------------------------------------------

    try:

        source.rename(
            destination
        )

        # ----------------------------------------------------
        # Verify rename.
        # ----------------------------------------------------

        if source.exists():

            return (
                f"I couldn't confirm that "
                f"'{item_name}' was renamed."
            )

        if not destination.exists():

            return (
                f"I couldn't confirm that "
                f"'{new_name}' was created."
            )

        return (
            f"Renamed '{item_name}' "
            f"to '{new_name}'."
        )

    except Exception as error:

        return (
            f"I couldn't rename "
            f"'{item_name}': {error}"
        )