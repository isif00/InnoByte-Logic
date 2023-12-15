from pytube import YouTube
from dotenv import load_dotenv
import moviepy.editor as mp
import os


load_dotenv()

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

    print(f"Fetching audio from Youtube URL: {url}")

    ensure_dir(output_video_file)
    ensure_dir(output_audio_file)

    video_stream = YouTube(url).streams.first()
    video_stream.download(filename=output_video_file)

    video = mp.VideoFileClip(output_video_file)
    video.audio.write_audiofile(output_audio_file, codec="pcm_s16le")

    print("Done fetching audio form YouTube")


def extract_wav_from_video(video_file, output_audio_file):
    """Extract WAV audio from given video file"""

    print(f"Extracting audio from video file: {video_file}")

    ensure_dir(output_audio_file)
    video = mp.VideoFileClip(video_file)
    video.audio.write_audiofile(output_audio_file, codec="pcm_s16le")

    print("Done extracting audio from video file")
