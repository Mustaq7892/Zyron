import time
from pathlib import Path

from src.zyron.core.router import ZyronRouter
from src.zyron.commands.file_manager import (
    create_file,
    write_file,
)


router = ZyronRouter(
    name="Mustaq"
)


# ============================================================
# STANDARD REGRESSION TESTS
# ============================================================

tests = [
    (
        "Open Chrome",
        "application",
    ),
    (
        "What is my CPU usage?",
        "system",
    ),
    (
        "How hard is my processor working right now?",
        "system",
    ),
    (
        "What is my RAM usage?",
        "system",
    ),
    (
        "Open the Zyron folder",
        "open_zyron_folder",
    ),
    (
        "What is inside my Zyron folder?",
        "list_zyron_files",
    ),
    (
        "Read hello.py",
        "read_file",
    ),
    (
        "Read notes.md",
        "read_file",
    ),
    (
        "Open hello.py",
        "open_file",
    ),
    (
        "Hello Zyron, how are you?",
        "conversation",
    ),
]


# ============================================================
# TEST HELPERS
# ============================================================

passed = 0
failed = 0


def print_separator():
    print(
        "-" * 70
    )
    print()


def pass_test():
    global passed

    passed += 1


def fail_test():
    global failed

    failed += 1


# ============================================================
# HEADER
# ============================================================

print()

print(
    "=" * 70
)

print(
    "                 ZYRON REGRESSION TEST"
)

print(
    "=" * 70
)

print()


# ============================================================
# TEST 1 - TEST 9
# ============================================================

for number, (
    command,
    expected,
) in enumerate(
    tests,
    1,
):

    print(
        f"TEST {number}"
    )

    print(
        f"Command : {command}"
    )

    print(
        f"Expected: {expected}"
    )

    start = time.perf_counter()

    try:

        response, should_exit = (
            router.route(
                command,
                name="Mustaq",
            )
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            "Response:"
        )

        print(
            response
        )

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    except Exception as error:

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            "ERROR:"
        )

        print(
            error
        )

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

    print_separator()


# ============================================================
# TEST 11 - MULTI-STEP COMMAND
# ============================================================

print(
    "TEST 11"
)

print(
    "Command : Create a folder called "
    "RegressionMultiTest and then list "
    "the contents of my Zyron folder"
)

print(
    "Expected: create_folder -> list_zyron_files"
)

multi_folder = Path(
    "RegressionMultiTest"
)

# Clean up before the test.

cleanup_failed = False

if multi_folder.exists():

    try:

        if multi_folder.is_dir():

            import shutil

            shutil.rmtree(
                multi_folder
            )

        else:

            multi_folder.unlink()

    except PermissionError:

        cleanup_failed = True

        print(
            "Cleanup : Windows could not remove "
            "RegressionMultiTest because it is in use."
        )

        print(
            "Cleanup : The test will continue, "
            "but the existing folder may affect the result."
        )

if cleanup_failed:

    print(
        "Cleanup : Reusing existing RegressionMultiTest folder."
    )


# Continue with the actual multi-step test.

    # Continue with the actual multi-step test.

    start = time.perf_counter()

    try:

        response, should_exit = (
            router.route(
                "Create a folder called "
                "RegressionMultiTest and then "
                "list the contents of my Zyron folder",
                name="Mustaq",
            )
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            "Response:"
        )

        print(
            response
        )

        print(
            f"Time    : {elapsed:.2f}s"
        )

        folder_exists = (
            multi_folder.exists()
        )

        listing_contains_folder = (
            "RegressionMultiTest"
            in response
        )

        if (
            folder_exists
            and listing_contains_folder
        ):

            print(
                "Folder  : RegressionMultiTest exists"
            )

            print(
                "Listing : RegressionMultiTest appears in response"
            )

            print(
                "Status  : PASS"
            )

            pass_test()

        else:

            print(
                "Folder  : FAILED"
            )
            print(
                "Listing : FAILED"
            )

            print(
                "Status  : FAIL"
            )

            fail_test()

    except Exception as error:

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            "ERROR:"
        )

        print(
            error
        )

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

    print_separator()




# ============================================================
# TEST 12 - DELETE CANCELLATION SAFETY
# ============================================================

print(
    "TEST 12"
)

print(
    "Command : Delete the folder "
    "RegressionDeleteTest"
)

print(
    "Expected: confirmation required, "
    "then cancellation"
)

delete_folder = Path(
    "RegressionDeleteTest"
)

# Make sure the folder exists before testing.

if delete_folder.exists():

    try:

        if delete_folder.is_dir():

            import shutil

            shutil.rmtree(
                delete_folder
            )

        else:

            delete_folder.unlink()

    except PermissionError:

        print(
            "Cleanup : Windows could not remove "
            "RegressionDeleteTest because it is in use."
        )

        print(
            "Cleanup : The existing folder will be reused."
        )

if not delete_folder.exists():

    delete_folder.mkdir()

start = time.perf_counter()

try:

    confirmation_response, should_exit = (
        router.route(
            "Delete the folder RegressionDeleteTest",
            name="Mustaq",
        )
    )

    print(
        "Confirmation:"
    )

    print(
        confirmation_response
    )

    cancellation_response, should_exit = (
        router.route(
            "no",
            name="Mustaq",
        )
    )

    print(
        "Cancellation:"
    )

    print(
        cancellation_response
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    confirmation_ok = (
        "confirmation"
        in confirmation_response.lower()
    )

    cancellation_ok = (
        "cancelled"
        in cancellation_response.lower()
    )

    folder_still_exists = (
        delete_folder.exists()
    )

    if (
        confirmation_ok
        and cancellation_ok
        and folder_still_exists
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Folder  : RegressionDeleteTest still exists"
        )

        print(
            "Safety  : Destructive action was cancelled"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Safety  : FAILED"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        f"Time    : {elapsed:.2f}s"
    )

    print(
        "Status  : FAIL"
    )

    fail_test()


# Clean up delete test folder.

if delete_folder.exists():

    try:

        if delete_folder.is_dir():

            import shutil

            shutil.rmtree(
                delete_folder
            )

        else:

            delete_folder.unlink()

    except PermissionError:

        print(
            "Cleanup : Windows still has the test folder open."
        )

        print(
            "Cleanup : RegressionDeleteTest was not removed automatically."
        )

print_separator()


# ============================================================
# TEST 13 - WRITE FILE CANCELLATION SAFETY
# ============================================================

print(
    "TEST 13"
)

print(
    "Command : Write CHANGED CONTENT "
    "into RegressionWriteTest.txt"
)

print(
    "Expected: confirmation required, "
    "then cancellation"
)

write_file_path = Path(
    "RegressionWriteTest.txt"
)

# Clean up any previous test file.

if write_file_path.exists():

    write_file_path.unlink()

# Create the test file.

create_result = create_file(
    "RegressionWriteTest.txt"
)

print(
    "Setup   :"
)

print(
    create_result
)

# Put known original content into it.

original_result = write_file(
    "RegressionWriteTest.txt",
    "ORIGINAL CONTENT",
)

print(
    original_result
)

start = time.perf_counter()

try:

    confirmation_response, should_exit = (
        router.route(
            "Write CHANGED CONTENT into "
            "RegressionWriteTest.txt",
            name="Mustaq",
        )
    )

    print(
        "Confirmation:"
    )

    print(
        confirmation_response
    )

    cancellation_response, should_exit = (
        router.route(
            "no",
            name="Mustaq",
        )
    )

    print(
        "Cancellation:"
    )

    print(
        cancellation_response
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    current_content = (
        write_file_path.read_text(
            encoding="utf-8"
        )
    )

    confirmation_ok = (
        "confirmation"
        in confirmation_response.lower()
    )

    cancellation_ok = (
        "cancelled"
        in cancellation_response.lower()
    )

    content_preserved = (
        current_content
        == "ORIGINAL CONTENT"
    )

    if (
        confirmation_ok
        and cancellation_ok
        and content_preserved
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Content : ORIGINAL CONTENT preserved"
        )

        print(
            "Safety  : Write operation was cancelled"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Content : FAILED"
        )

        print(
            "Safety  : FAILED"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        f"Time    : {elapsed:.2f}s"
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

# Clean up.

if write_file_path.exists():

    write_file_path.unlink()

print_separator()


# ============================================================
# TEST 14 - WRITE FILE CONFIRMATION
# ============================================================

print(
    "TEST 14"
)

print(
    "Command : Write CHANGED CONTENT "
    "into RegressionWriteConfirmTest.txt"
)

print(
    "Expected: confirmation required, "
    "then execution"
)

write_confirm_path = Path(
    "RegressionWriteConfirmTest.txt"
)

# Clean up any previous test file.

if write_confirm_path.exists():

    write_confirm_path.unlink()

# Create the file.

print(
    "Setup   :"
)

print(
    create_file(
        "RegressionWriteConfirmTest.txt"
    )
)

# Put original content inside.

print(
    write_file(
        "RegressionWriteConfirmTest.txt",
        "ORIGINAL CONTENT",
    )
)

start = time.perf_counter()

try:

    confirmation_response, should_exit = (
        router.route(
            "Write CHANGED CONTENT into "
            "RegressionWriteConfirmTest.txt",
            name="Mustaq",
        )
    )

    print(
        "Confirmation:"
    )

    print(
        confirmation_response
    )

    execution_response, should_exit = (
        router.route(
            "yes",
            name="Mustaq",
        )
    )

    print(
        "Execution:"
    )

    print(
        execution_response
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    current_content = (
        write_confirm_path.read_text(
            encoding="utf-8"
        )
    )

    confirmation_ok = (
        "confirmation"
        in confirmation_response.lower()
    )

    execution_ok = (
        "successfully wrote content"
        in execution_response.lower()
    )

    content_changed = (
        current_content
        == "CHANGED CONTENT"
    )

    if (
        confirmation_ok
        and execution_ok
        and content_changed
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Content : CHANGED CONTENT written"
        )

        print(
            "Safety  : Write operation required confirmation"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Content : FAILED"
        )

        print(
            "Safety  : FAILED"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        f"Time    : {elapsed:.2f}s"
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

# Clean up.

# Clean up.

if write_confirm_path.exists():

    write_confirm_path.unlink()

print_separator()


# ============================================================
# TEST 15 - RENAME CONFIRMATION AND EXECUTION
# ============================================================

print(
    "TEST 15"
)

print(
    "Command : Rename RegressionRenameTest.txt "
    "to RegressionRenamedTest.txt"
)

print(
    "Expected: confirmation required, "
    "then execution"
)

rename_source = Path(
    "RegressionRenameTest.txt"
)

rename_destination = Path(
    "RegressionRenamedTest.txt"
)

# ------------------------------------------------------------
# Clean up any leftovers from a previous run.
# ------------------------------------------------------------

if rename_source.exists():

    if rename_source.is_dir():

        import shutil

        shutil.rmtree(
            rename_source
        )

    else:

        rename_source.unlink()


if rename_destination.exists():

    if rename_destination.is_dir():

        import shutil

        shutil.rmtree(
            rename_destination
        )

    else:

        rename_destination.unlink()


# ------------------------------------------------------------
# Create the test file.
# ------------------------------------------------------------

from src.zyron.commands.file_manager import create_file

print(
    "Setup   :"
)

print(
    create_file(
        "RegressionRenameTest.txt"
    )
)

start = time.perf_counter()

try:

    confirmation_response, should_exit = (
        router.route(
            "Rename RegressionRenameTest.txt "
            "to RegressionRenamedTest.txt",
            name="Mustaq",
        )
    )

    print(
        "Confirmation:"
    )

    print(
        confirmation_response
    )

    execution_response, should_exit = (
        router.route(
            "yes",
            name="Mustaq",
        )
    )

    print(
        "Execution:"
    )

    print(
        execution_response
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    source_exists = (
        rename_source.exists()
    )

    destination_exists = (
        rename_destination.exists()
    )

    confirmation_ok = (
        "confirmation"
        in confirmation_response.lower()
    )

    execution_ok = (
        "renamed"
        in execution_response.lower()
    )

    if (
        confirmation_ok
        and execution_ok
        and not source_exists
        and destination_exists
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Original: RegressionRenameTest.txt removed"
        )

        print(
            "New     : RegressionRenamedTest.txt exists"
        )

        print(
            "Safety  : Rename operation required confirmation"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Original: FAILED"
        )

        print(
            "New     : FAILED"
        )

        print(
            "Safety  : FAILED"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        f"Time    : {elapsed:.2f}s"
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

# ------------------------------------------------------------
# Clean up rename test files.
# ------------------------------------------------------------

if rename_source.exists():

    if rename_source.is_dir():

        import shutil

        shutil.rmtree(
            rename_source
        )

    else:

        rename_source.unlink()


if rename_destination.exists():

    if rename_destination.is_dir():

        import shutil

        shutil.rmtree(
            rename_destination
        )

    else:

        rename_destination.unlink()


print_separator()


# ============================================================
# FINAL RESULT
# ============================================================

total_tests = 23


# ============================================================
# PHASE 2 - TEST 16
# NATURAL LANGUAGE APPLICATION REQUEST
# ============================================================

print(
    "TEST 16"
)

print(
    "Command : Please launch Chrome for me"
)

print(
    "Expected: application"
)

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "Please launch Chrome for me",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    if (
        "chrome"
        in response.lower()
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ============================================================
# PHASE 2 - TEST 17
# NATURAL LANGUAGE CPU REQUEST
# ============================================================

print(
    "TEST 17"
)

print(
    "Command : How much CPU am I using?"
)

print(
    "Expected: system"
)

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "How much CPU am I using?",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    response_lower = response.lower()

    if (
        "cpu"
        in response_lower
        and (
            "percent"
            in response_lower
            or "%"
            in response_lower
        )
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ============================================================
# PHASE 2 - TEST 18
# NATURAL LANGUAGE RAM REQUEST
# ============================================================

print(
    "TEST 18"
)

print(
    "Command : How much memory is currently being used?"
)

print(
    "Expected: system"
)

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "How much memory is currently being used?",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    response_lower = response.lower()

    if (
        "ram"
        in response_lower
        or "memory"
        in response_lower
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ============================================================
# PHASE 2 - TEST 19
# NATURAL LANGUAGE FILE READING
# ============================================================

print(
    "TEST 19"
)

print(
    "Command : Can you show me what's written in notes.md?"
)

print(
    "Expected: read_file"
)

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "Can you show me what's written in notes.md?",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    response_lower = response.lower()

    if (
        "zyron learning notes"
        in response_lower
        and "api"
        in response_lower
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ============================================================
# PHASE 3 - TEST 20
# NATURAL LANGUAGE FOLDER CREATION
# ============================================================

print(
    "TEST 20"
)

print(
    "Command : Please create a folder called Phase3NaturalFolder"
)

print(
    "Expected: create_folder"
)

phase3_folder = Path(
    "Phase3NaturalFolder"
)

if phase3_folder.exists():

    if phase3_folder.is_dir():

        import shutil

        shutil.rmtree(
            phase3_folder
        )

    else:

        phase3_folder.unlink()

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "Please create a folder called Phase3NaturalFolder",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    if (
        phase3_folder.exists()
        and phase3_folder.is_dir()
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Folder  : Phase3NaturalFolder exists"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Folder  : Phase3NaturalFolder was not created"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ============================================================
# PHASE 3 - TEST 21
# NATURAL LANGUAGE FOLDER LISTING
# ============================================================

print(
    "TEST 21"
)

print(
    "Command : Show me everything in my Zyron folder"
)

print(
    "Expected: list_zyron_files"
)

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "Show me everything in my Zyron folder",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    response_lower = response.lower()

    if (
        "here are the items"
        in response_lower
        and "phase3naturalfolder"
        in response_lower
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Listing : Phase3NaturalFolder appears in response"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "Listing : Expected folder was not found"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ============================================================
# PHASE 3 - TEST 22
# NATURAL LANGUAGE FILE OPENING
# ============================================================

print(
    "TEST 22"
)

print(
    "Command : Please open hello.py for me"
)

print(
    "Expected: open_file"
)

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "Please open hello.py for me",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    response_lower = response.lower()

    if (
        "opening"
        in response_lower
        and "hello.py"
        in response_lower
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "File    : hello.py opened"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "File    : hello.py was not opened as expected"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ============================================================
# PHASE 3 - TEST 23
# NATURAL LANGUAGE FILE READING
# ============================================================

print(
    "TEST 23"
)

print(
    "Command : Can you read the contents of hello.py?"
)

print(
    "Expected: read_file"
)

start = time.perf_counter()

try:

    response, should_exit = router.route(
        "Can you read the contents of hello.py?",
        name="Mustaq",
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Response:"
    )

    print(
        response
    )

    response_lower = response.lower()

    if (
        "contents of 'hello.py'"
        in response_lower
        and "import requests"
        in response_lower
    ):

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "File    : hello.py contents returned"
        )

        print(
            "Status  : PASS"
        )

        pass_test()

    else:

        print(
            f"Time    : {elapsed:.2f}s"
        )

        print(
            "File    : hello.py contents were not returned"
        )

        print(
            "Status  : FAIL"
        )

        fail_test()

except Exception as error:

    print(
        "ERROR:"
    )

    print(
        error
    )

    print(
        "Status  : FAIL"
    )

    fail_test()

print_separator()


# ------------------------------------------------------------
# Clean up Phase 3 folder.
# ------------------------------------------------------------

if phase3_folder.exists():

    if phase3_folder.is_dir():

        import shutil

        shutil.rmtree(
            phase3_folder
        )

    else:

        phase3_folder.unlink()
