from google.genai import types
import os

# --- ADA V2 TOOLS ---
generate_cad = {
    "name": "generate_cad",
    "description": "Generates a 3D CAD model based on a prompt.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {"type": "STRING", "description": "The description of the object to generate."}
        },
        "required": ["prompt"]
    }
}

iterate_cad = {
    "name": "iterate_cad",
    "description": "Modifies or iterates on the current CAD design based on user feedback.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {"type": "STRING", "description": "The changes or modifications to apply."}
        },
        "required": ["prompt"]
    }
}

run_web_agent = {
    "name": "run_web_agent",
    "description": "Opens a web browser and performs a task according to the prompt.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {"type": "STRING", "description": "The detailed instructions for the web browser agent."}
        },
        "required": ["prompt"]
    }
}

# --- MARK-XXX TOOLS ---
computer_control = {
    "name": "computer_control",
    "description": "Direct computer control: type, click, scroll, move, screenshot, etc.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "type | click | double_click | right_click | hotkey | press | scroll | move | screenshot | wait | clear_field | focus_window | screen_find | screen_click"},
            "text": {"type": "STRING", "description": "Text to type or paste"},
            "x": {"type": "INTEGER", "description": "X coordinate"},
            "y": {"type": "INTEGER", "description": "Y coordinate"},
            "keys": {"type": "STRING", "description": "Key combination (e.g. 'ctrl+c')"},
            "key": {"type": "STRING", "description": "Single key (e.g. 'enter')"},
            "direction": {"type": "STRING", "description": "up | down | left | right"},
            "amount": {"type": "INTEGER", "description": "Scroll amount"},
            "title": {"type": "STRING", "description": "Window title to focus"},
            "description": {"type": "STRING", "description": "Element description for AI finding"}
        },
        "required": ["action"]
    }
}

# --- TWILIO CALL TOOL ---
start_phone_call = {
    "name": "start_phone_call",
    "description": "Starts an AI-powered phone call to a given number.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "phone_number": {"type": "STRING", "description": "The phone number to call (E.164 format)."},
            "initial_phrase": {"type": "STRING", "description": "What JARVIS should say first when they pick up."}
        },
        "required": ["phone_number", "initial_phrase"]
    }
}

# --- FILE SYSTEM TOOLS ---
write_file = {
    "name": "write_file",
    "description": "Writes content to a file at the specified path.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "The path of the file to write to."},
            "content": {"type": "STRING", "description": "The content to write."}
        },
        "required": ["path", "content"]
    }
}

read_file = {
    "name": "read_file",
    "description": "Reads the content of a file.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "The path of the file to read."}
        },
        "required": ["path"]
    }
}

MEGA_TOOLS_DECLARATIONS = [
    generate_cad,
    iterate_cad,
    run_web_agent,
    computer_control,
    start_phone_call,
    write_file,
    read_file
]

def get_tools():
    return [{"google_search": {}}, {"function_declarations": MEGA_TOOLS_DECLARATIONS}]
