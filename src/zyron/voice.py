from pathlib import Path
import subprocess
import tempfile
import winsound
import sys


MODEL_PATH = Path("en_US-lessac-medium.onnx")


def speak(text):
    """Convert text to speech and play it directly."""

    text = str(text).strip()

    if not text:
        return

    if not MODEL_PATH.exists():
        print(f"Zyron voice model not found: {MODEL_PATH}")
        return

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ) as temp_file:
        output_file = Path(temp_file.name)

    try:
        command = [
            sys.executable,
            "-m",
            "piper",
            "-m",
            str(MODEL_PATH),
            "-f",
            str(output_file)
        ]

        subprocess.run(
            command,
            input=text,
            text=True,
            check=True
        )

        winsound.PlaySound(
            str(output_file),
            winsound.SND_FILENAME
        )

    except subprocess.CalledProcessError as error:
        print(f"Zyron voice generation failed: {error}")

    except Exception as error:
        print(f"Zyron voice error: {error}")

    finally:
        if output_file.exists():
            output_file.unlink()