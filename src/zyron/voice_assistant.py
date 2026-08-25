import re

import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel

from .core.router import ZyronRouter
from .voice import speak


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 16000
CHANNELS = 1

# Your working microphone
MICROPHONE_DEVICE = 1

# WebRTC VAD settings
VAD_AGGRESSIVENESS = 2

# Audio frame size.
# WebRTC VAD supports 10, 20, or 30 ms.
FRAME_DURATION_MS = 30

# Maximum time we listen for one command.
MAX_RECORD_SECONDS = 8

# How long speech must continue before recording starts.
START_SPEECH_FRAMES = 3

# How many silent frames end a command.
END_SILENCE_FRAMES = 15

# Minimum amount of audio required.
MIN_AUDIO_SECONDS = 0.30

# Minimum RMS level for a usable recording.
MIN_RMS = 0.012

# Faster-Whisper
MODEL_SIZE = "small"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"


# ============================================================
# WEBRTC VAD
# ============================================================

print("Loading WebRTC VAD...")

vad = webrtcvad.Vad(
    VAD_AGGRESSIVENESS
)

print("WebRTC VAD loaded.")
print()


# ============================================================
# LOAD FASTER-WHISPER
# ============================================================

print("Loading Faster-Whisper model...")

model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE,
)

print("Faster-Whisper model loaded.")
print()


# ============================================================
# USER NAME NORMALIZATION
# ============================================================

def normalize_user_name(name):
    """
    Normalize the name supplied when Zyron starts.

    Example:

        mustaq
        MUSTAQ
        Mustaq

    all become:

        Mustaq
    """

    if not name:
        return "User"

    name = str(name).strip()

    if not name:
        return "User"

    # Known spelling normalization.
    #
    # This is intentionally small. We do not want to
    # maintain a giant list of Whisper corrections.
    known_names = {
        "mustaq": "Mustaq",
    }

    normalized = name.lower()

    if normalized in known_names:
        return known_names[normalized]

    return name[0].upper() + name[1:]


# ============================================================
# TRANSCRIPTION NORMALIZATION
# ============================================================

def normalize_transcription(text):
    """
    Perform very conservative transcription cleanup.

    We intentionally avoid aggressive correction because
    incorrectly changing user commands can be dangerous.

    Example:

        xyron
        XYRON
        Xyron

    become:

        Zyron

    when the word is clearly the project name.
    """

    if not text:
        return ""

    text = str(text).strip()

    if not text:
        return ""

    # --------------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    # --------------------------------------------------------
    # Normalize common Zyron transcription variations.
    #
    # Keep this conservative.
    # --------------------------------------------------------

    text = re.sub(
        r"\bxyron\b",
        "Zyron",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bzyron\b",
        "Zyron",
        text,
        flags=re.IGNORECASE,
    )

    return text


# ============================================================
# AUDIO RMS
# ============================================================

def calculate_rms(audio):
    """
    Calculate the RMS level of an audio signal.
    """

    if audio is None:
        return 0.0

    audio = np.asarray(
        audio,
        dtype=np.float32,
    )

    if audio.size == 0:
        return 0.0

    return float(
        np.sqrt(
            np.mean(
                np.square(audio)
            )
        )
    )


# ============================================================
# RECORD AUDIO WITH WEBRTC VAD
# ============================================================

def record_audio():
    """
    Record one voice command using WebRTC VAD.

    Recording starts after speech is detected and stops after
    enough silence is detected.

    Returns:
        numpy.ndarray containing mono float32 audio
    """

    print("[Zyron is listening...]")
    print()
    print("Speak now...")

    frame_size = int(
        SAMPLE_RATE
        * FRAME_DURATION_MS
        / 1000
    )

    frame_duration_seconds = (
        FRAME_DURATION_MS / 1000
    )

    max_frames = int(
        MAX_RECORD_SECONDS
        / frame_duration_seconds
    )

    start_speech_frames = START_SPEECH_FRAMES
    end_silence_frames = END_SILENCE_FRAMES

    audio_frames = []

    speech_started = False

    consecutive_speech = 0
    consecutive_silence = 0

    # --------------------------------------------------------
    # Open microphone stream.
    # --------------------------------------------------------

    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=MICROPHONE_DEVICE,
            blocksize=frame_size,
        ) as stream:

            for _ in range(max_frames):

                frame, overflowed = (
                    stream.read(frame_size)
                )

                if overflowed:
                    print(
                        "Warning: microphone "
                        "buffer overflow."
                    )

                frame = np.asarray(
                    frame,
                    dtype=np.float32,
                ).reshape(-1)

                # ------------------------------------------------
                # Convert float32 audio to PCM int16 for WebRTC.
                # ------------------------------------------------

                clipped = np.clip(
                    frame,
                    -1.0,
                    1.0,
                )

                pcm16 = (
                    clipped * 32767
                ).astype(
                    np.int16
                )

                is_speech = vad.is_speech(
                    pcm16.tobytes(),
                    SAMPLE_RATE,
                )

                # ------------------------------------------------
                # Speech detection.
                # ------------------------------------------------

                if is_speech:

                    consecutive_speech += 1
                    consecutive_silence = 0

                else:

                    consecutive_speech = 0

                    if speech_started:
                        consecutive_silence += 1

                # ------------------------------------------------
                # Start recording after stable speech.
                # ------------------------------------------------

                if (
                    not speech_started
                    and consecutive_speech
                    >= start_speech_frames
                ):

                    speech_started = True

                    # Include the current frame.
                    audio_frames.append(
                        frame.copy()
                    )

                    continue

                # ------------------------------------------------
                # Once speech starts, keep collecting audio.
                # ------------------------------------------------

                if speech_started:

                    audio_frames.append(
                        frame.copy()
                    )

                    # ------------------------------------------------
                    # End after enough silence.
                    # ------------------------------------------------

                    if (
                        consecutive_silence
                        >= end_silence_frames
                    ):

                        break

    except Exception as error:

        print()
        print(
            "Microphone recording error:"
        )
        print(error)
        print()

        return np.array(
            [],
            dtype=np.float32,
        )

    # --------------------------------------------------------
    # No speech detected.
    # --------------------------------------------------------

    if not audio_frames:

        print(
            "No speech detected."
        )

        return np.array(
            [],
            dtype=np.float32,
        )

    # --------------------------------------------------------
    # Combine frames.
    # --------------------------------------------------------

    audio = np.concatenate(
        audio_frames
    ).astype(
        np.float32
    )

    # --------------------------------------------------------
    # Remove excessive trailing silence.
    #
    # WebRTC already stops recording after silence, so this
    # is mainly a cleanup operation.
    # --------------------------------------------------------

    return audio


# ============================================================
# TRANSCRIPTION CONFIDENCE
# ============================================================

MIN_TRANSCRIPTION_LOGPROB = -1.20
MAX_COMPRESSION_RATIO = 2.40
MAX_NO_SPEECH_PROBABILITY = 0.75

DESTRUCTIVE_MIN_CONFIDENCE = 0.70

LAST_TRANSCRIPTION_CONFIDENCE = 0.0


def calculate_transcription_confidence(
    no_speech_prob,
    avg_logprob,
    compression_ratio,
):
    """
    Calculate confidence from Faster-Whisper quality signals.

    This does not inspect particular words or phrases.
    """

    if avg_logprob <= -2.0:
        logprob_score = 0.0
    elif avg_logprob >= -0.20:
        logprob_score = 1.0
    else:
        logprob_score = (
            (avg_logprob + 2.0) / 1.80
        )

    speech_score = max(
        0.0,
        min(1.0, 1.0 - no_speech_prob),
    )

    if compression_ratio >= 3.0:
        compression_score = 0.0
    elif compression_ratio <= 1.0:
        compression_score = 1.0
    else:
        compression_score = (
            (3.0 - compression_ratio) / 2.0
        )

    confidence = (
        (logprob_score * 0.50)
        + (speech_score * 0.30)
        + (compression_score * 0.20)
    )

    return max(0.0, min(1.0, confidence))


# ============================================================
# TRANSCRIBE AUDIO
# ============================================================

def transcribe(audio):
    """
    Convert recorded audio into text.

    The returned value remains a string so existing Zyron
    callers continue to work. The latest dynamic confidence
    is stored in LAST_TRANSCRIPTION_CONFIDENCE.
    """

    global LAST_TRANSCRIPTION_CONFIDENCE

    LAST_TRANSCRIPTION_CONFIDENCE = 0.0

    if audio is None:
        return ""

    audio = np.asarray(
        audio,
        dtype=np.float32,
    )

    if audio.size == 0:
        return ""

    rms = calculate_rms(audio)

    print(f"Audio RMS: {rms:.5f}")

    if rms < MIN_RMS:
        print(
            "Audio level too low. "
            "Ignoring possible background noise."
        )
        return ""

    duration = len(audio) / SAMPLE_RATE

    print(
        f"Audio duration: {duration:.2f} seconds"
    )

    if duration < MIN_AUDIO_SECONDS:
        print("Audio recording too short.")
        return ""

    try:

        segments, info = model.transcribe(
            audio,
            language="en",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True,
            condition_on_previous_text=False,
        )

        accepted_segments = []

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            no_speech_prob = float(
                getattr(
                    segment,
                    "no_speech_prob",
                    1.0,
                )
            )

            avg_logprob = float(
                getattr(
                    segment,
                    "avg_logprob",
                    -999.0,
                )
            )

            compression_ratio = float(
                getattr(
                    segment,
                    "compression_ratio",
                    999.0,
                )
            )

            confidence = calculate_transcription_confidence(
                no_speech_prob,
                avg_logprob,
                compression_ratio,
            )

            print()
            print("Whisper segment:")
            print(f"  Text: {text}")
            print(
                f"  no_speech_prob: "
                f"{no_speech_prob:.3f}"
            )
            print(
                f"  avg_logprob: "
                f"{avg_logprob:.3f}"
            )
            print(
                f"  compression_ratio: "
                f"{compression_ratio:.3f}"
            )
            print(
                f"  confidence: "
                f"{confidence:.3f}"
            )

            if no_speech_prob > MAX_NO_SPEECH_PROBABILITY:
                print(
                    "Segment rejected: "
                    "high no-speech probability."
                )
                continue

            if avg_logprob < MIN_TRANSCRIPTION_LOGPROB:
                print(
                    "Segment rejected: "
                    "low average log probability."
                )
                continue

            if compression_ratio > MAX_COMPRESSION_RATIO:
                print(
                    "Segment rejected: "
                    "suspicious compression ratio."
                )
                continue

            if confidence < 0.45:
                print(
                    "Segment rejected: "
                    f"low confidence ({confidence:.3f})."
                )
                continue

            accepted_segments.append(
                (text, confidence)
            )

        if not accepted_segments:
            print(
                "No reliable transcription "
                "was accepted."
            )
            return ""

        text = " ".join(
            item[0]
            for item in accepted_segments
        ).strip()

        # Use the weakest accepted segment as the overall
        # confidence for safety.
        LAST_TRANSCRIPTION_CONFIDENCE = min(
            item[1]
            for item in accepted_segments
        )

        return normalize_transcription(text)

    except Exception as error:

        print()
        print("Transcription error:")
        print(error)
        print()

        return ""


# ============================================================
# COMMAND SAFETY
# ============================================================

def validate_voice_command(
    text,
    confidence=None,
):
    """
    Validate a transcription before sending it to the router.

    No target-specific or phrase-specific transcription
    blacklist is used.

    Potentially destructive operations require stronger
    dynamic transcription confidence.
    """

    if not text:
        return False, ""

    text = str(text).strip()

    if not text:
        return False, ""

    normalized = " ".join(
        text.split()
    ).strip().lower()

    if not normalized:
        return False, ""

    if len(normalized) <= 1:
        return False, ""

    if confidence is None:
        confidence = LAST_TRANSCRIPTION_CONFIDENCE

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    # Determine potentially destructive intent from the
    # operation type, not from the target memory.
    destructive = normalized.startswith(
        (
            "forget ",
            "forgot ",
            "delete ",
            "clear ",
        )
    )

    if destructive:

        parts = normalized.split(" ", 1)

        if len(parts) < 2:
            print(
                "Destructive command rejected: "
                "no target supplied."
            )
            return False, ""

        target = parts[1].strip()

        if len(target) < 3:
            print(
                "Destructive command rejected: "
                "target is too short."
            )
            return False, ""

        if confidence < DESTRUCTIVE_MIN_CONFIDENCE:
            print(
                "Destructive command rejected: "
                f"confidence {confidence:.3f} is below "
                f"{DESTRUCTIVE_MIN_CONFIDENCE:.2f}."
            )
            return False, ""

    return True, text

# ============================================================
# MAIN VOICE ASSISTANT
# ============================================================

def main():

    print("================================")
    print("       ZYRON VOICE ASSISTANT")
    print("================================")
    print()

    print(
        f"Model: {MODEL_SIZE}"
    )

    print(
        f"Device: {DEVICE}"
    )

    print(
        f"Compute type: {COMPUTE_TYPE}"
    )

    print(
        f"Microphone device: {MICROPHONE_DEVICE}"
    )

    print(
        "Recording mode: WebRTC VAD"
    )

    print(
        f"VAD aggressiveness: "
        f"{VAD_AGGRESSIVENESS}"
    )

    print()

    # ========================================================
    # ASK USER NAME
    # ========================================================

    name = input(
        "What is your name? "
    ).strip()

    name = normalize_user_name(
        name
    )

    print()

    print(
        f"Hello. I am Zyron, your personal AI assistant. "
        f"How can I help you, {name}?"
    )

    print()

    # ========================================================
    # CREATE ONE ROUTER FOR THE ENTIRE SESSION
    # ========================================================

    router = ZyronRouter(
        name=name
    )

    # ========================================================
    # STARTUP MESSAGE
    # ========================================================

    startup_message = (
        f"Hello {name}. "
        "I am Zyron. "
        "Voice mode is ready."
    )

    print(
        f"Zyron: {startup_message}"
    )

    speak(
        startup_message
    )

    print()

    # ========================================================
    # CONTINUOUS VOICE LOOP
    # ========================================================

    while True:

        try:

            # ------------------------------------------------
            # Record until speech starts and then stops.
            # ------------------------------------------------

            audio = record_audio()

            print()

            # ------------------------------------------------
            # Nothing detected.
            # ------------------------------------------------

            if (
                audio is None
                or len(audio) == 0
            ):

                print(
                    "I couldn't understand that."
                )

                print()

                continue

            # ------------------------------------------------
            # Transcribe.
            # ------------------------------------------------

            print(
                "Transcribing..."
            )

            text = transcribe(
                audio
            )

            # ------------------------------------------------
            # Nothing understood.
            # ------------------------------------------------

            if not text:

                print(
                    "I couldn't understand that."
                )

                print()

                continue

            # ------------------------------------------------
            # Display recognized speech.
            # ------------------------------------------------

            print()

            print(
                f"You said: {text}"
            )

            print(
                f"Transcription confidence: "
                f"{LAST_TRANSCRIPTION_CONFIDENCE:.3f}"
            )

            # ------------------------------------------------
            # Validate transcription before routing.
            #
            # This is important because the microphone/
            # Whisper result must NOT automatically become
            # an executable Zyron command.
            # ------------------------------------------------

            is_valid, validated_text = (
                validate_voice_command(
                    text,
                    LAST_TRANSCRIPTION_CONFIDENCE,
                )
            )

            if not is_valid:

                print(
                    "Voice command rejected."
                )

                print(
                    "I couldn't reliably understand "
                    "that command."
                )

                print()

                continue

            # ------------------------------------------------
            # Send validated command to Zyron.
            # ------------------------------------------------

            response, should_exit = (
                router.route(
                    validated_text,
                    name=name,
                )
            )

            # ------------------------------------------------
            # Empty response.
            # ------------------------------------------------

            if not response:

                if should_exit:
                    break

                print()

                continue

            # ------------------------------------------------
            # Display Zyron response.
            # ------------------------------------------------

            print()

            print(
                f"Zyron: {response}"
            )

            # ------------------------------------------------
            # Speak Zyron response.
            # ------------------------------------------------

            speak(
                response
            )

            # ------------------------------------------------
            # Exit.
            # ------------------------------------------------

            if should_exit:

                break

            print()

        # ====================================================
        # KEYBOARD INTERRUPT
        # ====================================================

        except KeyboardInterrupt:

            print()

            print(
                "Zyron voice assistant stopped."
            )

            break

        # ====================================================
        # GENERAL ERROR
        # ====================================================

        except Exception as error:

            print()

            print(
                "Voice assistant error:"
            )

            print(
                error
            )

            print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()