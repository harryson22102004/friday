import sys
import asyncio

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend dir is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mega_jarvis import MegaAudioLoop

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
fast_app = FastAPI()
fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app = socketio.ASGIApp(sio, fast_app)

audio_loop = None

@fast_app.get("/status")
async def status():
    return {"status": "FRIDAY ONLINE", "version": "MEGA-1.0"}

@sio.event
async def connect(sid, environ):
    print(f"[SERVER] Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"[SERVER] Client disconnected: {sid}")

@sio.event
async def start_audio(sid, data=None):
    global audio_loop
    if audio_loop:
        await sio.emit('status', {'msg': 'ALREADY RUNNING'}, room=sid)
        return

    def on_transcription(data):
        asyncio.create_task(sio.emit('transcription', data))

    def on_error(msg):
        asyncio.create_task(sio.emit('error', {'msg': msg}))

    def on_status(msg):
        asyncio.create_task(sio.emit('status', {'msg': msg}))

    audio_loop = MegaAudioLoop(
        on_transcription=on_transcription,
        on_error=on_error,
        on_status=on_status
    )
    asyncio.create_task(audio_loop.run())
    await sio.emit('status', {'msg': 'SYSTEM ACTIVE — FRIDAY LISTENING'}, room=sid)
    print("[SERVER] Audio loop started.")

@sio.event
async def stop_audio(sid):
    global audio_loop
    if audio_loop:
        audio_loop.stop()
        audio_loop = None
        await sio.emit('status', {'msg': 'SYSTEM STANDBY'}, room=sid)
        print("[SERVER] Audio loop stopped.")

@sio.event
async def user_input(sid, data):
    """Handle text input from the UI."""
    text = data.get('text', '')
    if not text:
        return
    print(f"[SERVER] Text input: {text}")
    global audio_loop
    if not audio_loop or not audio_loop.session:
        await sio.emit('error', {'msg': 'Start voice first — click the orb!'}, room=sid)
        return
    try:
        await audio_loop.session.send_client_content(
            turns={"parts": [{"text": text}]},
            turn_complete=True
        )
    except Exception as e:
        await sio.emit('error', {'msg': f'Send failed: {str(e)}'}, room=sid)

@sio.event
async def ping(sid):
    await sio.emit('pong', {}, room=sid)

@sio.event
async def capture_vision(sid):
    print("[SERVER] Triggering Vision Engine...")
    import subprocess
    subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'capture_face.py')])
    await sio.emit('status', {'msg': 'VISION ENGINE ACTIVE - PRESS SPACE TO CAPTURE'}, room=sid)

if __name__ == "__main__":
    print("=" * 60)
    print("  FRIDAY JARVIS — MEGA AI SYSTEM")
    print("  Backend: http://localhost:5000")
    print("  Open friday.html in your browser to start!")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="warning")
