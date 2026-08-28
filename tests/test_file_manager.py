
from src.zyron.commands.file_manager import (
    PROJECT_ROOT,
    write_file,
)


def test_write_file_refuses_overwrite_by_default():
    test_file = PROJECT_ROOT / "zyron_test_overwrite.txt"

    try:
        test_file.write_text(
            "ORIGINAL CONTENT",
            encoding="utf-8",
        )

        result = write_file(
            "zyron_test_overwrite.txt",
            "NEW CONTENT",
        )

        assert "already exists" in result
        assert (
            test_file.read_text(
                encoding="utf-8"
            )
            == "ORIGINAL CONTENT"
        )

    finally:
        if test_file.exists():
            test_file.unlink()


def test_write_file_allows_explicit_overwrite():
    test_file = PROJECT_ROOT / "zyron_test_overwrite.txt"

    try:
        test_file.write_text(
            "ORIGINAL CONTENT",
            encoding="utf-8",
        )

        result = write_file(
            "zyron_test_overwrite.txt",
            "NEW CONTENT",
            overwrite=True,
        )

        assert "Successfully wrote content" in result
        assert (
            test_file.read_text(
                encoding="utf-8"
            )
            == "NEW CONTENT"
        )

    finally:
        if test_file.exists():
            test_file.unlink()
