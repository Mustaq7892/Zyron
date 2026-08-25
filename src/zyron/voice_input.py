import numpy as np
import sounddevice as sd

from faster_whisper import WhisperModel


# ============================================================
# ZYRON VOICE INPUT
# ============================================================

# ------------------------------------------------------------
# MICROPHONE
# ------------------------------------------------------------

SAMPLE_RATE = 16000
CHANNELS = 1

# Your tested working microphone.
MICROPHONE_DEVICE = 1


# ------------------------------------------------------------
# WHISPER
# ------------------------------------------------------------

MODEL_SIZE = "small"

DEVICE = "cpu"
COMPUTE_TYPE = "int8"


# ------------------------------------------------------------
# AUDIO BLOCKS
# ------------------------------------------------------------

BLOCK_DURATION = 0.05

BLOCK_SIZE = int(
    SAMPLE_RATE * BLOCK_DURATION
)


# ------------------------------------------------------------
# LISTENING LIMITS
# ------------------------------------------------------------

MAX_WAIT_SECONDS = 8.0

MAX_COMMAND_SECONDS = 10.0

END_SILENCE_SECONDS = 0.8


# ------------------------------------------------------------
# BASIC AUDIO THRESHOLDS
# ------------------------------------------------------------

# These are deliberately conservative.
#
# Your microphone's measured silence was extremely quiet,
# so we don't need to treat tiny fluctuations as speech.

MIN_RMS = 0.0025

MIN_PEAK = 0.0120


# ------------------------------------------------------------
# DYNAMIC NOISE MULTIPLIERS
# ------------------------------------------------------------

RMS_MULTIPLIER = 4.0

PEAK_MULTIPLIER = 2.0


# ------------------------------------------------------------
# SPEECH START REQUIREMENT
# ------------------------------------------------------------

# 6 x 0.05 seconds = 0.30 seconds
#
# A single noise spike therefore cannot start recording.

START_BLOCKS = 6

# Number of consecutive silent blocks required
# to consider the user's command finished.
END_SILENCE_BLOCKS = max(
    1,
    int(END_SILENCE_SECONDS / BLOCK_DURATION)
)


# ------------------------------------------------------------
# WHISPER VALIDATION
# ------------------------------------------------------------

MAX_ALLOWED_NO_SPEECH = 0.30

MIN_ALLOWED_LOG_PROB = -0.90

MIN_SPEECH_DURATION = 0.35


# ============================================================
# LOAD WHISPER
# ============================================================

print(
    "Loading Faster-Whisper model..."
)

try:

    model = WhisperModel(
        MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
    )

    print(
        "Faster-Whisper model loaded."
    )

except Exception as error:

    print(
        f"Failed to load Faster-Whisper model: {error}"
    )

    model = None


# ============================================================
# AUDIO HELPERS
# ============================================================

def get_rms(audio):
    """
    Calculate RMS audio level.
    """

    if audio is None:

        return 0.0

    if len(audio) == 0:

        return 0.0

    audio = np.asarray(
        audio,
        dtype=np.float32,
    )

    return float(
        np.sqrt(
            np.mean(
                np.square(audio)
            )
        )
    )


def get_peak(audio):
    """
    Calculate peak audio level.
    """

    if audio is None:

        return 0.0

    if len(audio) == 0:

        return 0.0

    audio = np.asarray(
        audio,
        dtype=np.float32,
    )

    return float(
        np.max(
            np.abs(audio)
        )
    )


# ============================================================
# MICROPHONE CALIBRATION
# ============================================================

def calibrate_microphone(stream):

    calibration_seconds = 1.0

    calibration_blocks = max(
        1,
        int(
            calibration_seconds
            / BLOCK_DURATION
        ),
    )

    rms_values = []

    peak_values = []

    for _ in range(
        calibration_blocks
    ):

        data, overflowed = stream.read(
            BLOCK_SIZE
        )

        if overflowed:

            print(
                "Warning: microphone "
                "buffer overflow."
            )

        audio = np.asarray(
            data,
            dtype=np.float32,
        ).reshape(-1)

        rms_values.append(
            get_rms(audio)
        )

        peak_values.append(
            get_peak(audio)
        )

    background_rms = float(
        np.median(
            rms_values
        )
    )

    background_peak = float(
        np.median(
            peak_values
        )
    )

    rms_threshold = max(
        MIN_RMS,
        background_rms
        * RMS_MULTIPLIER,
    )

    peak_threshold = max(
        MIN_PEAK,
        background_peak
        * PEAK_MULTIPLIER,
    )

    print(
        f"Background RMS: "
        f"{background_rms:.6f}"
    )

    print(
        f"Background peak: "
        f"{background_peak:.6f}"
    )

    print(
        f"RMS threshold: "
        f"{rms_threshold:.6f}"
    )

    print(
        f"Peak threshold: "
        f"{peak_threshold:.6f}"
    )

    return (
        rms_threshold,
        peak_threshold,
    )


# ============================================================
# SPEECH BLOCK DETECTION
# ============================================================

def is_speech_block(
    audio,
    rms_threshold,
    peak_threshold,
):
    """
    Decide whether one audio block contains
    sufficiently strong audio.
    """

    rms = get_rms(audio)

    peak = get_peak(audio)

    rms_is_strong = (
        rms >= rms_threshold
    )

    peak_is_strong = (
        peak >= peak_threshold
    )

    return (
        rms_is_strong
        and
        peak_is_strong
    )


# ============================================================
# TRIM SILENCE
# ============================================================

def trim_audio(
    audio,
    threshold,
):
    """
    Remove silence from the beginning and
    end of the recording.

    This is real trimming; the previous version
    only calculated RMS/peak without actually
    trimming the audio.
    """

    if audio is None:

        return None

    audio = np.asarray(
        audio,
        dtype=np.float32,
    ).reshape(-1)

    if len(audio) == 0:

        return None

    absolute_audio = np.abs(
        audio
    )

    active_indices = np.where(
        absolute_audio >= threshold
    )[0]

    if len(active_indices) == 0:

        return None

    first = int(
        active_indices[0]
    )

    last = int(
        active_indices[-1]
    )

    # Add a small amount of padding so
    # we don't cut off the beginning/end
    # of a spoken word.

    padding = int(
        0.15 * SAMPLE_RATE
    )

    first = max(
        0,
        first - padding
    )

    last = min(
        len(audio) - 1,
        last + padding
    )

    return audio[
        first:last + 1
    ]


# ============================================================
# RECORD COMMAND
# ============================================================

def record_command():

    print()

    print(
        "Listening... Speak now."
    )

    try:

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="float32",
            channels=CHANNELS,
            device=MICROPHONE_DEVICE,
        ) as stream:

            (
                rms_threshold,
                peak_threshold,
            ) = calibrate_microphone(
                stream
            )

            print()

            print(
                "Waiting for speech..."
            )

            # ------------------------------------------------
            # WAIT FOR SPEECH
            # ------------------------------------------------

            max_wait_blocks = int(
                MAX_WAIT_SECONDS
                / BLOCK_DURATION
            )

            candidate_blocks = []

            consecutive_speech = 0

            speech_started = False

            for _ in range(
                max_wait_blocks
            ):

                data, overflowed = stream.read(
                    BLOCK_SIZE
                )

                if overflowed:

                    print(
                        "Warning: microphone "
                        "buffer overflow."
                    )

                audio = np.asarray(
                    data,
                    dtype=np.float32,
                ).reshape(-1)

                if is_speech_block(
                    audio,
                    rms_threshold,
                    peak_threshold,
                ):

                    candidate_blocks.append(
                        audio.copy()
                    )

                    consecutive_speech += 1

                else:

                    candidate_blocks.clear()

                    consecutive_speech = 0

                # ------------------------------------------------
                # Require sustained speech.
                # ------------------------------------------------

                if (
                    consecutive_speech
                    >= START_BLOCKS
                ):

                    speech_started = True

                    print(
                        "Speech detected."
                    )

                    break

            # ------------------------------------------------
            # Nothing detected.
            # ------------------------------------------------

            if not speech_started:

                print(
                    "I didn't detect any speech."
                )

                return None

            # ------------------------------------------------
            # Continue recording.
            # ------------------------------------------------

            recorded_blocks = list(
                candidate_blocks
            )

            silence_blocks = 0

            max_command_blocks = int(
                MAX_COMMAND_SECONDS
                / BLOCK_DURATION
            )

            while (
                len(recorded_blocks)
                < max_command_blocks
            ):

                data, overflowed = stream.read(
                    BLOCK_SIZE
                )

                if overflowed:

                    print(
                        "Warning: microphone "
                        "buffer overflow."
                    )

                audio = np.asarray(
                    data,
                    dtype=np.float32,
                ).reshape(-1)

                recorded_blocks.append(
                    audio.copy()
                )

                if is_speech_block(
                    audio,
                    rms_threshold,
                    peak_threshold,
                ):

                    silence_blocks = 0

                else:

                    silence_blocks += 1

                if (
                    silence_blocks
                    >= END_SILENCE_BLOCKS
                ):

                    break

            # ------------------------------------------------
            # Combine recording.
            # ------------------------------------------------

            if not recorded_blocks:

                return None

            audio = np.concatenate(
                recorded_blocks
            )

            raw_rms = get_rms(
                audio
            )

            raw_peak = get_peak(
                audio
            )

            raw_duration = (
                len(audio)
                / SAMPLE_RATE
            )

            print()

            print(
                f"Raw audio RMS: "
                f"{raw_rms:.6f}"
            )

            print(
                f"Raw audio peak: "
                f"{raw_peak:.6f}"
            )

            print(
                f"Raw duration: "
                f"{raw_duration:.2f} seconds"
            )

            # ------------------------------------------------
            # Initial safety validation.
            # ------------------------------------------------

            if (
                raw_duration
                < MIN_SPEECH_DURATION
            ):

                print(
                    "Recording rejected:"
                )

                print(
                    "Recording was too short."
                )

                return None

            if raw_rms < MIN_RMS:

                print(
                    "Recording rejected:"
                )

                print(
                    "Audio signal was too weak."
                )

                return None

            if raw_peak < MIN_PEAK:

                print(
                    "Recording rejected:"
                )

                print(
                    "Audio peak was too weak."
                )

                return None

            # ------------------------------------------------
            # ACTUAL SILENCE TRIMMING
            # ------------------------------------------------

            trim_threshold = max(
                MIN_RMS,
                rms_threshold
            )

            trimmed_audio = trim_audio(
                audio,
                trim_threshold,
            )

            if trimmed_audio is None:

                print(
                    "Recording rejected:"
                )

                print(
                    "No usable speech region "
                    "was found."
                )

                return None

            audio = trimmed_audio

            final_rms = get_rms(
                audio
            )

            final_peak = get_peak(
                audio
            )

            final_duration = (
                len(audio)
                / SAMPLE_RATE
            )

            print()

            print(
                f"Trimmed audio RMS: "
                f"{final_rms:.6f}"
            )

            print(
                f"Trimmed audio peak: "
                f"{final_peak:.6f}"
            )

            print(
                f"Trimmed duration: "
                f"{final_duration:.2f} seconds"
            )

            if (
                final_duration
                < MIN_SPEECH_DURATION
            ):

                print(
                    "Recording rejected:"
                )

                print(
                    "Usable speech was too short."
                )

                return None

            return audio

    except Exception as error:

        print()

        print(
            f"Microphone error: {error}"
        )

        return None


# ============================================================
# WHISPER TRANSCRIPTION
# ============================================================

def transcribe(audio):

    if model is None:

        return ""

    if audio is None:

        return ""

    if len(audio) == 0:

        return ""

    print()

    print(
        "Transcribing..."
    )

    try:

        segments, info = model.transcribe(

            audio,

            language="en",

            beam_size=5,

            best_of=5,

            temperature=0,

            condition_on_previous_text=False,

            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 150,
            },

            no_speech_threshold=0.6,

        )

        segments = list(
            segments
        )

        if not segments:

            print(
                "Whisper returned no speech."
            )

            return ""

        # ----------------------------------------------------
        # Collect useful segment information.
        # ----------------------------------------------------

        valid_segments = []

        for segment in segments:

            text = (
                segment.text
                or ""
            ).strip()

            if not text:

                continue

            valid_segments.append(
                segment
            )

        if not valid_segments:

            print(
                "Whisper produced no usable text."
            )

            return ""

        # ----------------------------------------------------
        # Build transcription.
        # ----------------------------------------------------

        texts = []

        log_probs = []

        no_speech_probs = []

        segment_durations = []

        for segment in valid_segments:

            text = (
                segment.text
                or ""
            ).strip()

            texts.append(
                text
            )

            if (
                segment.avg_logprob
                is not None
            ):

                log_probs.append(
                    float(
                        segment.avg_logprob
                    )
                )

            if (
                segment.no_speech_prob
                is not None
            ):

                no_speech_probs.append(
                    float(
                        segment.no_speech_prob
                    )
                )

            try:

                duration = (
                    float(segment.end)
                    -
                    float(segment.start)
                )

                segment_durations.append(
                    duration
                )

            except Exception:

                pass

        text = " ".join(
            texts
        )

        text = " ".join(
            text.split()
        ).strip()

        if not text:

            return ""

        # ----------------------------------------------------
        # Statistics.
        # ----------------------------------------------------

        average_log_prob = (

            float(
                np.mean(
                    log_probs
                )
            )

            if log_probs

            else None
        )

        average_no_speech = (

            float(
                np.mean(
                    no_speech_probs
                )
            )

            if no_speech_probs

            else None
        )

        total_segment_duration = (

            float(
                np.sum(
                    segment_durations
                )
            )

            if segment_durations

            else 0.0
        )

        print()

        print(
            "Raw Whisper transcription:"
        )

        print(
            text
        )

        if average_log_prob is not None:

            print(
                "Average Whisper "
                "log probability: "
                f"{average_log_prob:.3f}"
            )

        if average_no_speech is not None:

            print(
                "Average no-speech "
                "probability: "
                f"{average_no_speech:.3f}"
            )

        print(
            f"Whisper segments: "
            f"{len(valid_segments)}"
        )

        print(
            f"Whisper speech duration: "
            f"{total_segment_duration:.2f} seconds"
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        # ----------------------------------------------------
        # RULE 1
        #
        # High no-speech probability means Whisper itself
        # thinks this may not contain speech.
        # ----------------------------------------------------

        if (
            average_no_speech is not None
            and average_no_speech >= MAX_ALLOWED_NO_SPEECH
            and average_log_prob is not None
            and average_log_prob < MIN_ALLOWED_LOG_PROB
        ):

            print()
            print(
                "Whisper rejected the recording "
                "because both speech probability "
                "and transcription confidence "
                "were poor."
            )

            return ""

        # ----------------------------------------------------
        # RULE 2
        #
        # Reject extremely poor-confidence transcription.
        # ----------------------------------------------------

        if (
            average_log_prob is not None
            and
            average_log_prob
            < MIN_ALLOWED_LOG_PROB
        ):

            print()

            print(
                "Whisper rejected the "
                "recording."
            )

            print(
                f"Confidence was too low: "
                f"{average_log_prob:.3f}"
            )

            print(
                f"Required minimum: "
                f"{MIN_ALLOWED_LOG_PROB:.3f}"
            )

            return ""

        # ----------------------------------------------------
        # RULE 3
        #
        # Whisper must identify an actual speech region.
        # ----------------------------------------------------

        if (
            total_segment_duration
            < MIN_SPEECH_DURATION
        ):

            print()

            print(
                "Whisper rejected the "
                "recording because the "
                "detected speech duration "
                "was too short."
            )

            return ""

        # ----------------------------------------------------
        # RULE 4
        #
        # Do not accept an empty/meaningless result.
        # ----------------------------------------------------

        if len(text) < 2:

            print()

            print(
                "Whisper produced an "
                "extremely short result."
            )

            return ""

        return text

    except Exception as error:

        print()

        print(
            f"Whisper error: {error}"
        )

        return ""


# ============================================================
# PUBLIC LISTEN FUNCTION
# ============================================================

def listen():

    if model is None:

        return ""

    audio = record_command()

    if audio is None:

        return ""

    text = transcribe(
        audio
    )

    if not text:

        print()

        print(
            "I couldn't confidently "
            "understand that."
        )

        return ""

    print()

    print(
        f"You said: {text}"
    )

    return text


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "================================"
    )

    print(
        " ZYRON VOICE INPUT TEST"
    )

    print(
        "================================"
    )

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
        f"Microphone device: "
        f"{MICROPHONE_DEVICE}"
    )

    while True:

        print()

        print(
            "[Zyron is listening...]"
        )

        text = listen()

        if text:

            print()

            print(
                "Accepted command:"
            )

            print(
                text
            )

        print()

        choice = input(
            "Press ENTER to test again, "
            "or type EXIT: "
        ).strip().lower()

        if choice == "exit":

            print(
                "Voice test stopped."
            )

            break