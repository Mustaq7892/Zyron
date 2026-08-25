import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 16000
CHANNELS = 1

# Your laptop microphone
MICROPHONE_DEVICE = 1

# Record for this many seconds
RECORD_SECONDS = 8

# Whisper model
MODEL_SIZE = "small"

# Your computer does not have NVIDIA CUDA available.
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


# ============================================================
# LOAD FASTER-WHISPER
# ============================================================

print("Loading Faster-Whisper model...")
print()

model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE,
)

print("Faster-Whisper model loaded.")
print()


# ============================================================
# RECORD AUDIO
# ============================================================

def record_audio():

    print("Speak now...")

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        device=MICROPHONE_DEVICE,
    )

    sd.wait()

    return np.squeeze(audio)


# ============================================================
# TRANSCRIBE AUDIO
# ============================================================

def transcribe(audio):

    segments, info = model.transcribe(
        audio,
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )

    text_parts = []

    for segment in segments:

        text = segment.text.strip()

        if text:
            text_parts.append(text)

    return " ".join(text_parts).strip()


# ============================================================
# TEST
# ============================================================

def main():

    print("================================")
    print(" FASTER-WHISPER VOICE TEST")
    print("================================")
    print()

    print(f"Model: {MODEL_SIZE}")
    print(f"Device: {DEVICE}")
    print(f"Compute type: {COMPUTE_TYPE}")
    print(f"Microphone device: {MICROPHONE_DEVICE}")
    print()

    audio = record_audio()

    print()
    print("Recording finished.")
    print("Transcribing...")
    print()

    text = transcribe(audio)

    if text:
        print("You said:")
        print(text)
    else:
        print("I couldn't understand the recording.")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()