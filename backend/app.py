import base64
import json
import os
import subprocess
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
NOTES_FILE = BACKEND_DIR / "notes.txt"
OUTPUT_WAV = BACKEND_DIR / "output.wav"
SYNTH_BINARY = BACKEND_DIR / ("synth.exe" if os.name == "nt" else "synth")

MAX_TOTAL_DURATION_SECONDS = 20.0
MIN_FREQ_HZ = 20.0
MAX_FREQ_HZ = 20000.0

app = Flask(__name__)
CORS(app)

client = anthropic.Anthropic()

SYSTEM_PROMPT = (
    "You are a melody composer. Given a plain-language description of a mood, "
    "genre, or tune, translate it into real musical note frequencies using "
    "standard equal-temperament pitches (A4 = 440 Hz). Output JSON only — no "
    "prose, no markdown fences, no explanation. The sum of all \"dur\" values "
    "across all notes must not exceed 20 seconds."
)

NOTES_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "freq": {"type": "number"},
                    "dur": {"type": "number"},
                },
                "required": ["freq", "dur"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "notes"],
    "additionalProperties": False,
}


def generate_notes(user_request):
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_request}],
        output_config={"format": {"type": "json_schema", "schema": NOTES_SCHEMA}},
    )
    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    title = data.get("title") or "Untitled"
    notes = data.get("notes") or []
    return title, notes


def validate_and_cap_notes(notes):
    """Filter out-of-range notes, then truncate the list to a 20s total duration."""
    valid = []
    for note in notes:
        try:
            freq = float(note["freq"])
            dur = float(note["dur"])
        except (KeyError, TypeError, ValueError):
            continue
        if MIN_FREQ_HZ <= freq <= MAX_FREQ_HZ and dur > 0:
            valid.append({"freq": freq, "dur": dur})

    capped = []
    total = 0.0
    for note in valid:
        if total + note["dur"] > MAX_TOTAL_DURATION_SECONDS:
            break
        capped.append(note)
        total += note["dur"]
    return capped


def write_notes_file(notes):
    with open(NOTES_FILE, "w") as f:
        for note in notes:
            f.write(f"{note['freq']} {note['dur']}\n")


def run_synth():
    if not SYNTH_BINARY.exists():
        raise RuntimeError(f"synth binary not found at {SYNTH_BINARY}")
    result = subprocess.run(
        [str(SYNTH_BINARY)],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"synth binary failed: {result.stderr}")


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "ok",
        "message": "Walkman backend is running. POST to /generate to synthesize audio.",
    })


@app.route("/generate", methods=["POST"])
def generate():
    try:
        body = request.get_json(silent=True) or {}
        user_request = (body.get("request") or "").strip()
        if not user_request:
            return jsonify({"error": "Missing 'request' field"}), 400

        title, raw_notes = generate_notes(user_request)
        notes = validate_and_cap_notes(raw_notes)
        if not notes:
            return jsonify({"error": "No valid notes were generated for that request"}), 500

        write_notes_file(notes)
        run_synth()

        if not OUTPUT_WAV.exists():
            return jsonify({"error": "synth did not produce output.wav"}), 500

        with open(OUTPUT_WAV, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("ascii")

        return jsonify({
            "title": title,
            "notes": notes,
            "audio_base64": audio_b64,
        })
    except anthropic.AuthenticationError:
        return jsonify({"error": "Invalid or missing ANTHROPIC_API_KEY"}), 502
    except anthropic.RateLimitError:
        return jsonify({"error": "Anthropic API rate limit exceeded, try again shortly"}), 502
    except anthropic.APIStatusError as e:
        return jsonify({"error": f"Anthropic API error: {e.message}"}), 502
    except anthropic.APIConnectionError:
        return jsonify({"error": "Could not reach the Anthropic API"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
