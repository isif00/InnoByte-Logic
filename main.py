import os
import re
import json

from bson import json_util
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient

from ai_meeting_transcription.transcription import *
from meets_pv.pv_generator import generate_pv


load_dotenv()

USER = os.getenv("USER")
PASS = os.getenv("PASS")
CONNECTION_STRING = f"mongodb+srv://{USER}:{PASS}@cluster0.tspozkq.mongodb.net/?retryWrites=true&w=majority"


client = MongoClient(CONNECTION_STRING)
db = client.innobyte
transcriptions = db.transcriptions

print("[INFO] Connected to MongoDB successfully")

app = Flask(__name__)


def parse_subtitle_text(subtitle_text):
    # Regular expression to extract timecodes and speaker lines
    pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}\.\d{2}),(\d{2}:\d{2}:\d{2}\.\d{2})\n(\S+):(.+?)(?=\n\n|\Z)",
        re.DOTALL,
    )

    matches = pattern.findall(subtitle_text)

    subtitles = []
    for match in matches:
        start_time, end_time, speaker, speech = match
        subtitle_info = {
            "start_time": start_time,
            "end_time": end_time,
            "speaker": speaker,
            "speech": speech.strip(),
        }
        subtitles.append(subtitle_info)

    return subtitles


def parse_json(data):
    return json.loads(json_util.dumps(data, default="str"))


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

    parsed_output = parse_subtitle_text(output)
    print(parsed_output)

    transcriptions.insert_many(parse_json(parsed_output))
    # inserted_transcription = transcriptions.find_one({"_id": transcription.inserted_id})
    # inserted_transcription["_id"] = str(inserted_transcription["_id"])

    return jsonify(parsed_output)


@app.route("/pv", methods=["GET"])
def get_pv():
    speech = ""
    cursor = transcriptions.find({})
    for transcription in cursor:
        # speech = transcription["speech"]
        speech = speech + f"{transcription['speech']}"

    print("generating pv ...")
    pv = generate_pv(speech)
    return pv


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
