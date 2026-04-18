import asyncio
import os
import sys

# Force UTF-8 for Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import time
from dotenv import load_dotenv
import sounddevice as sd
import numpy as np
from google import genai
from google.genai import types

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(http_options={"api_version": "v1beta"}, api_key=API_KEY)

from mega_tools import get_tools

# Lazy imports - optional modules
try:
    from actions.computer_control import computer_control as _computer_control
    _COMPUTER_OK = True
except Exception as e:
    print(f"[WARN] computer_control unavailable: {e}")
    _COMPUTER_OK = False

try:
    from cad_agent import CadAgent
    _CAD_OK = True
except Exception as e:
    print(f"[WARN] CadAgent unavailable: {e}")
    _CAD_OK = False

try:
    from web_agent import WebAgent
    _WEB_OK = True
except Exception as e:
    print(f"[WARN] WebAgent unavailable (install playwright): {e}")
    _WEB_OK = False

FORMAT_DTYPE = 'int16'
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

# Best native audio model
MODEL = "models/gemini-2.5-flash-native-audio-latest"

SYSTEM_PROMPT = """You are FRIDAY, a next-generation AI assistant — the fusion of JARVIS, ADA, and MARK. 
You are professional, witty, and devastatingly efficient. Address the user as "Sir" always.
You can control the computer, browse the web, generate 3D models, make phone calls, and more.
Never say you can't do something — find a way or tell Sir what you need.
Be concise. No filler words. Only results."""

class MegaAudioLoop:
    def __init__(self, on_transcription=None, on_cad_data=None, on_web_data=None, 
                 on_error=None, on_status=None, input_device_index=None):
        self.on_transcription = on_transcription
        self.on_cad_data = on_cad_data
        self.on_web_data = on_web_data
        self.on_error = on_error
        self.on_status = on_status
        self.input_device_index = input_device_index

        self.audio_in_queue = None
        self.out_queue = None
        self.stop_event = asyncio.Event()
        self.session = None
        self.paused = False
        self.playback_stream = None

        # Agents
        self.cad_agent = CadAgent() if _CAD_OK else None
        self.web_agent = WebAgent() if _WEB_OK else None

    def stop(self):
        self.stop_event.set()
        if self.playback_stream:
            try:
                self.playback_stream.stop()
                self.playback_stream.close()
            except Exception:
                pass

    def get_config(self):
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction=SYSTEM_PROMPT,
            tools=get_tools(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"  # Deep authoritative voice
                    )
                )
            )
        )

    async def run(self):
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()

        try:
            print(f"[FRIDAY] Connecting to Gemini Live API...")
            async with client.aio.live.connect(model=MODEL, config=self.get_config()) as session:
                self.session = session
                print(f"[FRIDAY] Connected! Online and listening.")
                if self.on_status:
                    self.on_status("FRIDAY ONLINE")

                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self.listen_audio())
                    tg.create_task(self.send_realtime())
                    tg.create_task(self.receive_audio())
                    tg.create_task(self.play_audio())
        except* Exception as eg:
            for err in eg.exceptions:
                print(f"[FRIDAY] Error: {err}")
                if self.on_error:
                    self.on_error(str(err))

    async def listen_audio(self):
        """Capture mic audio and push to send queue."""
        loop = asyncio.get_event_loop()

        def callback(indata, frames, t, status):
            if self.paused or self.stop_event.is_set():
                return
            if status:
                print(f"[MIC] {status}")
            data_bytes = indata.tobytes()
            asyncio.run_coroutine_threadsafe(
                self.out_queue.put({"data": data_bytes, "mime_type": "audio/pcm"}),
                loop
            )

        with sd.InputStream(
            device=self.input_device_index,
            channels=CHANNELS,
            samplerate=SEND_SAMPLE_RATE,
            callback=callback,
            dtype=FORMAT_DTYPE,
            blocksize=CHUNK_SIZE
        ):
            print("[FRIDAY] Microphone active.")
            while not self.stop_event.is_set():
                await asyncio.sleep(0.05)

    async def send_realtime(self):
        """Send queued audio/data to Gemini session."""
        while not self.stop_event.is_set():
            try:
                msg = await asyncio.wait_for(self.out_queue.get(), timeout=0.5)
                await self.session.send_realtime_input(media=msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[FRIDAY] Send error: {e}")
                break

    async def play_audio(self):
        """Play received audio chunks."""
        self.playback_stream = sd.OutputStream(
            channels=CHANNELS,
            samplerate=RECEIVE_SAMPLE_RATE,
            dtype=FORMAT_DTYPE
        )
        self.playback_stream.start()
        print("[FRIDAY] Speaker active.")
        while not self.stop_event.is_set():
            try:
                data = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.5)
                arr = np.frombuffer(data, dtype=FORMAT_DTYPE)
                self.playback_stream.write(arr)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[FRIDAY] Playback error: {e}")

    async def receive_audio(self):
        """Receive and process all responses from Gemini."""
        print("[FRIDAY] Receive loop started.")
        in_text_buf = []
        out_text_buf = []

        async for response in self.session.receive():
            if self.stop_event.is_set():
                break

            # Audio chunks
            if response.data:
                self.audio_in_queue.put_nowait(response.data)

            # Transcriptions
            if response.server_content:
                sc = response.server_content
                if sc.input_transcription and sc.input_transcription.text:
                    txt = sc.input_transcription.text.strip()
                    if txt:
                        in_text_buf.append(txt)
                        if self.on_transcription:
                            self.on_transcription({"sender": "User", "text": txt})
                        print(f"[Sir]: {txt}")

                if sc.output_transcription and sc.output_transcription.text:
                    txt = sc.output_transcription.text.strip()
                    if txt:
                        out_text_buf.append(txt)
                        if self.on_transcription:
                            self.on_transcription({"sender": "FRIDAY", "text": txt})
                        print(f"[FRIDAY]: {txt}")

                if sc.turn_complete:
                    in_text_buf.clear()
                    out_text_buf.clear()

            # Tool calls
            if response.tool_call:
                fn_responses = []
                for fc in response.tool_call.function_calls:
                    print(f"[FRIDAY] Tool call: {fc.name}")
                    result = await self.execute_tool(fc)
                    fn_responses.append(
                        types.FunctionResponse(name=fc.name, id=fc.id, response=result)
                    )
                await self.session.send_tool_response(function_responses=fn_responses)

    async def execute_tool(self, fc):
        """Execute a tool call from the AI."""
        name = fc.name
        args = dict(fc.args or {})
        loop = asyncio.get_event_loop()

        try:
            if name == "computer_control" and _COMPUTER_OK:
                result = await loop.run_in_executor(None, lambda: _computer_control(args))
                return {"result": str(result)}

            elif name == "generate_cad" and self.cad_agent:
                prompt = args.get("prompt", "")
                asyncio.create_task(self._run_cad(prompt))
                return {"result": "CAD generation started in background, Sir."}

            elif name == "run_web_agent" and self.web_agent:
                prompt = args.get("prompt", "")
                asyncio.create_task(self._run_web(prompt))
                return {"result": "Web agent launched, Sir."}

            elif name == "write_file":
                path = args.get("path", "output.txt")
                content = args.get("content", "")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"result": f"File '{path}' written successfully."}

            elif name == "read_file":
                path = args.get("path", "")
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"result": content[:5000]}  # Limit to 5k chars

            elif name == "start_phone_call":
                return {"result": "Phone call feature requires Twilio credentials. Please configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env"}

            else:
                return {"result": f"Tool '{name}' acknowledged. Feature may need additional setup."}

        except Exception as e:
            print(f"[FRIDAY] Tool error ({name}): {e}")
            return {"result": f"Tool failed: {str(e)}"}

    async def _run_cad(self, prompt):
        try:
            result = await self.cad_agent.generate_prototype(prompt)
            if result and self.on_cad_data:
                self.on_cad_data(result)
        except Exception as e:
            print(f"[FRIDAY] CAD error: {e}")

    async def _run_web(self, prompt):
        try:
            result = await self.web_agent.run_task(prompt)
            if result and self.on_web_data:
                self.on_web_data(result)
        except Exception as e:
            print(f"[FRIDAY] Web agent error: {e}")
