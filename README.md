# Walkman Melody Player

A text prompt is translated into musical notes by the Anthropic API, synthesized into a `.wav` file by a C++ program, and played back through a retro Walkman-themed web UI.

## Setup

### 1. Install Python dependencies

```
cd backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Compile the C++ synthesizer

```
g++ backend/synth.cpp -o backend/synth.exe
```

Run this from PowerShell, not Git Bash.

### 3. Add your Anthropic API key

Copy `backend/.env.example` to `backend/.env` and set your key:

```
ANTHROPIC_API_KEY=your_key_here
```

## Running

### Start the backend

```
cd backend
venv\Scripts\python.exe app.py
```

Runs on `http://127.0.0.1:5000`.

### Start the frontend

In a separate terminal:

```
cd frontend
python -m http.server 8000
```

Open `http://127.0.0.1:8000` in a browser.

Both the backend and frontend servers must stay running while you use the app. Opening `frontend/index.html` directly by double-click will not work, since it loads over `file://` and cannot reach the backend.

## Notes

- `backend/notes.txt` and `backend/output.wav` are written on each request and are not tracked in git.
- `backend/.env` holds the API key and is not tracked in git.
- The C++ synthesizer reads `backend/notes.txt` (one `frequency duration` pair per line) and writes `backend/output.wav`.
