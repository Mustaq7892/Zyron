from unittest.mock import patch

from src.zyron.commands.app_manager import handle_application_command


@patch("src.zyron.commands.app_manager.subprocess.Popen")
def test_open_chrome_is_allowed(mock_popen):
    result = handle_application_command("open chrome")

    assert result == "Opening Google Chrome."
    mock_popen.assert_called_once()


def test_show_information_about_chrome_does_not_open():
    result = handle_application_command(
        "show me information about chrome"
    )

    assert result is None


def test_dont_open_chrome_is_rejected():
    result = handle_application_command("dont open chrome")

    assert result is None


def test_do_not_open_chrome_is_rejected():
    result = handle_application_command("do not open chrome")

    assert result is None


def test_dont_launch_notepad_is_rejected():
    result = handle_application_command(
        "please dont launch notepad"
    )

    assert result is None