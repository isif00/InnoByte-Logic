from flask import Flask, request, jsonify
from transformers import pipeline
from pyannote.audio import Pipeline
from pytube import YouTube
from pydub import AudioSegment
from dotenv import load_dotenv
import moviepy.editor as mp
import datetime
import logging
import os
import shutil


load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    format="%(asctime)s %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S"
)

# Tokens, etc
# Hugging Face token: https://huggingface.co/docs/hub/security-tokens#user-access-tokens
HUGGINGFACE_AUTH_TOKEN = os.getenv("HUGGINGFACE_AUTH_TOKEN")
logging.info(f"Hugging Face token: {HUGGINGFACE_AUTH_TOKEN}")

TEMP_VIDEO_FILE = "temp/input.mp4"
TEMP_AUDIO_FILE = "temp/input.wav"
TEMP_DIARIZATION_FILE = "temp/diarization.rttm"


def ensure_dir(path):
    """Make sure director from the given path exists"""
    dir = os.path.dirname(path)
    if dir:
        os.makedirs(dir, exist_ok=True)


def fetch_youtube(url, output_video_file, output_audio_file):
    """Fetch WAV audio from given youtube URL"""

    logging.info(f"Fetching audio from Youtube URL: {url}")

    ensure_dir(output_video_file)
    ensure_dir(output_audio_file)

    video_stream = YouTube(url).streams.first()
    video_stream.download(filename=output_video_file)

    video = mp.VideoFileClip(output_video_file)
    video.audio.write_audiofile(output_audio_file, codec="pcm_s16le")

    logging.info("Done fetching audio form YouTube")


TIMESTAMP_FORMAT = "%H:%M:%S.%f"
base_time = datetime.datetime(1970, 1, 1)


def format_timestamp(seconds):
    """Format timestamp in SubViewer format: https://wiki.videolan.org/SubViewer/"""

    date = base_time + datetime.timedelta(seconds=seconds)
    return date.strftime(TIMESTAMP_FORMAT)[:-4]


def extract_audio_track(input_file, start_time, end_time, track_file):
    """Extract and save part of given audio file"""

    # Load the WAV file
    audio = AudioSegment.from_wav(input_file)

    # Calculate the start and end positions in milliseconds
    start_ms = start_time * 1000
    end_ms = end_time * 1000

    # Extract the desired segment
    track = audio[start_ms:end_ms]

    track.export(track_file, format="mp3")


def generate_speaker_diarization(audio_file):
    """Generate speaker diarization for given audio file"""

    logging.info(f"Generating speaker diarization... audio file: {audio_file}")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.0", use_auth_token=HUGGINGFACE_AUTH_TOKEN
    )

    result = pipeline(audio_file)

    logging.info("Done generating spearer diarization")

    with open(TEMP_DIARIZATION_FILE, "w") as rttm:
        result.write_rttm(rttm)

    logging.info(
        f"Wrote diarization file: {TEMP_DIARIZATION_FILE}",
    )

    return result


def generate_transcription(diarization, model, collar):
    """Generate transcription from given diarization object"""

    logging.info(f"Generating transcription... model: {model}")

    pipe = pipeline(
        "automatic-speech-recognition",
        model=f"openai/whisper-{model}",
        chunk_length_s=30,
        device="cpu",
    )

    # Create directory for tracks
    shutil.rmtree("output-tracks", ignore_errors=True)
    os.mkdir("output-tracks")

    result = []
    for turn, _, speaker in diarization.support(collar).itertracks(yield_label=True):
        part_file = f"output-tracks/{round(turn.start, 2)}-{speaker}.mp3"
        part_path = os.path.join(os.curdir, part_file)
        extract_audio_track(TEMP_AUDIO_FILE, turn.start, turn.end, part_file)

        part_data = None
        with open(part_path, "rb") as audio_content:
            part_data = audio_content.read()

        output = pipe(part_data, batch_size=8, return_timestamps=False)
        text = output["text"]

        result.append(
            {
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,
                "text": text.strip(),
                "track_path": part_path,
            }
        )

    logging.info(f"Done generating transcripion tracks: {len(result)}")
    return result


def format_transcription(transcription):
    """Format transcription in SubViewer format: https://wiki.videolan.org/SubViewer/"""

    result = ""
    for t in transcription:
        result += f"{format_timestamp(t['start'])},{format_timestamp(t['end'])}\n{t['speaker']}: {t['text']}\n\n"
    return result


@app.route("/transcribe", methods=["POST"])
def transcribe():
    youtube_url = request.get_json()
    youtube_url = youtube_url["youtube_url"]
    print(youtube_url)

    fetch_youtube(
        youtube_url,
        output_audio_file=TEMP_AUDIO_FILE,
        output_video_file=TEMP_VIDEO_FILE,
    )

    diarization = generate_speaker_diarization(TEMP_AUDIO_FILE)
    logging.info(f"Reusing local dirization file... {TEMP_DIARIZATION_FILE}")

    transcription = generate_transcription(diarization, "base", 0.5)
    output = format_transcription(transcription)

    print(output)
    return jsonify(output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
