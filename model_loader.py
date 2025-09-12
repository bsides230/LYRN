import argparse
import json
import os
import time
import sys
from pathlib import Path
from llama_cpp import Llama
from file_lock import SimpleFileLock

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
SETTINGS_PATH = SCRIPT_DIR / "settings.json"
TRIGGER_FILE = SCRIPT_DIR / "chat_trigger.txt"

def log(message):
    """Prints a message to stderr for the GUI to capture."""
    print(f"MODEL_LOADER: {message}", file=sys.stderr, flush=True)

def load_settings():
    """Loads settings from the shared settings.json file."""
    if not SETTINGS_PATH.exists():
        log("FATAL: settings.json not found.")
        sys.exit(1)
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"FATAL: Error loading settings.json: {e}")
        sys.exit(1)

def build_message_list(settings: dict, chat_folder_path: str, exclude_file: str = None) -> list:
    """
    Constructs the list of messages for the chat model, parsing chat history
    from the chat directory.
    """
    # 1. Get the system prompt from the master prompt file.
    master_prompt_path = SCRIPT_DIR / "build_prompt" / "master_prompt.txt"
    try:
        with open(master_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        log(f"WARNING: Master prompt file not found at {master_prompt_path}. Using a default system prompt.")
        system_prompt = "You are a helpful assistant."

    messages = [{"role": "system", "content": system_prompt}]

    # 2. Get the chat history from files.
    if not os.path.isdir(chat_folder_path):
        log(f"WARNING: Chat directory not found at {chat_folder_path}")
        return messages

    try:
        chat_files = sorted([f for f in os.listdir(chat_folder_path) if f.startswith("chat_") and f.endswith(".txt")])
        if exclude_file:
            chat_files = [f for f in chat_files if f != exclude_file]
    except OSError as e:
        log(f"ERROR: Could not list files in chat directory {chat_folder_path}: {e}")
        return messages

    for filename in chat_files:
        filepath = os.path.join(chat_folder_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # The file format is: user\n{user_content}\n\nmodel\n{assistant_content}
            if not content.startswith("user\n"):
                log(f"WARNING: Skipping malformed chat file {filename}: does not start with 'user\\n'.")
                continue

            model_separator = "\n\nmodel\n"
            separator_pos = content.find(model_separator)

            if separator_pos == -1:
                # This could be the file currently being generated, which is fine.
                log(f"INFO: Skipping chat file {filename} as it seems incomplete (no model response).")
                continue

            user_content = content[len("user\n"):separator_pos].strip()
            assistant_content = content[separator_pos + len(model_separator):].strip()

            if user_content:
                messages.append({"role": "user", "content": user_content})
            if assistant_content:
                messages.append({"role": "assistant", "content": assistant_content})

        except Exception as e:
            log(f"ERROR: Failed to read or parse chat file {filename}: {e}")

    return messages

def process_chat_request(llm: Llama, settings: dict, chat_file_path_str: str):
    """
    Processes a chat request by building a proper message list and streaming the
    response back into the specified chat file.
    """
    log(f"Processing request for chat file: {chat_file_path_str}")
    chat_file_path = Path(chat_file_path_str)
    chat_folder = chat_file_path.parent

    try:
        # 1. Build message history from all previous chat files.
        messages = build_message_list(settings, str(chat_folder), exclude_file=chat_file_path.name)

        # 2. Get the current user prompt from the trigger file content.
        with open(chat_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith("user\n"):
            raise ValueError("Malformed chat trigger file: does not start with 'user\\n'.")

        model_separator = "\n\nmodel\n"
        separator_pos = content.find(model_separator)
        if separator_pos == -1:
            raise ValueError("Malformed chat trigger file: no 'model' separator.")

        user_content = content[len("user\n"):separator_pos].strip()

        # 3. Add the current user message to the list.
        messages.append({"role": "user", "content": user_content})

        # 4. Call the model with the structured message list.
        stream = llm.create_chat_completion(
            messages=messages,
            max_tokens=settings.get("active", {}).get("max_tokens", 4096),
            temperature=settings.get("active", {}).get("temperature", 0.7),
            top_p=settings.get("active", {}).get("top_p", 0.95),
            top_k=settings.get("active", {}).get("top_k", 40),
            stream=True,
        )

        # 5. Stream the response back to the same chat file.
        with open(chat_file_path, "a", encoding="utf-8") as f:
            for token_data in stream:
                content_part = token_data['choices'][0]['delta'].get('content', '')
                if content_part:
                    f.write(content_part)
                    f.flush()
            f.write("\n")

        log(f"Finished streaming response to {chat_file_path.name}")

    except Exception as e:
        log(f"Error processing chat request for {chat_file_path.name}: {e}")
        try:
            with open(chat_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n[MODEL_LOADER_ERROR]: {e}\n")
        except Exception as write_e:
            log(f"Failed to write error to chat file: {write_e}")


def handle_startup_prompt(llm: Llama, settings: dict):
    """Handles the special '###startup###' prompt."""
    log("Processing '###startup###' request.")
    try:
        master_prompt_path = SCRIPT_DIR / "build_prompt" / "master_prompt.txt"
        with open(master_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "System bootup complete. Confirm initialization."}
        ]

        # Run a single generation to load the model and process the system prompt.
        _ = llm.create_chat_completion(messages=messages, max_tokens=1)
        log("Startup prompt processed successfully.")
    except Exception as e:
        log(f"Error processing startup prompt: {e}")


def watch_for_trigger(llm: Llama, settings: dict):
    """Main loop that watches for the chat_trigger.txt file."""
    log(f"Watching for trigger file: {TRIGGER_FILE}")
    while True:
        if TRIGGER_FILE.exists():
            try:
                with open(TRIGGER_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                # Immediately delete the trigger file to prevent reprocessing
                TRIGGER_FILE.unlink()

                if content == "###startup###":
                    handle_startup_prompt(llm, settings)
                elif content:
                    process_chat_request(llm, settings, content)
                else:
                    log("Trigger file was empty. Ignoring.")

            except Exception as e:
                log(f"Error processing trigger file: {e}")
                if TRIGGER_FILE.exists():
                    try:
                        TRIGGER_FILE.unlink()
                    except OSError:
                        pass # Ignore if it's already gone
        time.sleep(0.1)

def main():
    """
    Main function to set up and run the model loader.
    """
    parser = argparse.ArgumentParser(description="LYRN-AI Model Loader")
    parser.add_argument("--model-path", type=str, required=True, help="Path to the GGUF model file.")
    parser.add_argument("--n_ctx", type=int, default=8192, help="Context size.")
    parser.add_argument("--n_threads", type=int, default=8, help="Number of threads.")
    parser.add_argument("--n_gpu_layers", type=int, default=0, help="Number of GPU layers.")
    args = parser.parse_args()

    log("--- LYRN-AI Model Loader (File-based) ---")
    log(f"Model Path: {args.model_path}")
    log(f"Context Size: {args.n_ctx}")
    log(f"Threads: {args.n_threads}")
    log(f"GPU Layers: {args.n_gpu_layers}")
    log("-----------------------------------------")

    settings = load_settings()

    # --- Load the actual Llama model ---
    try:
        log("Loading model...")
        llm = Llama(
            model_path=args.model_path,
            n_ctx=args.n_ctx,
            n_threads=args.n_threads,
            n_gpu_layers=args.n_gpu_layers,
            verbose=True # Llama.cpp will print its own logs to stderr
        )
        log("Model loaded successfully.")
    except Exception as e:
        log(f"FATAL: Failed to load model. Error: {e}")
        sys.exit(1) # Exit if the model can't be loaded

    # Start the main watch loop
    watch_for_trigger(llm, settings)

if __name__ == "__main__":
    main()
