from flask import Flask
from ai_meeting_transcription/web-ui import process_video

app = Flask(__name__)


@app.route("/end_meet")
def Hello():
    output = process_video()
    return output