import os
import json

# Constants
SOURCE_FILE = os.path.join("to_process", "conversations.json")
OUTPUT_DIR = "queued_chunks"
CHUNK_PREFIX = "conversations_part_"
MAX_CHUNK_SIZE = 0.5 * 1024 * 1024  # 0.5 MB

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"[❌] File not found: {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        try:
            conversations = json.load(f)
        except Exception as e:
            print(f"[❌] Failed to parse JSON: {e}")
            return

    chunk = []
    chunk_count = 1
    current_size = 0

    for convo in conversations:
        convo_data = json.dumps(convo, indent=2)
        size = len(convo_data.encode("utf-8"))

        if current_size + size > MAX_CHUNK_SIZE:
            if chunk:
                out_path = os.path.join(OUTPUT_DIR, f"{CHUNK_PREFIX}{chunk_count:02}.json")
                with open(out_path, "w", encoding="utf-8") as f_out:
                    json.dump(chunk, f_out, indent=2)
                print(f"✅ Wrote chunk {chunk_count} ({len(chunk)} conversations) → {out_path}")
                chunk_count += 1
                chunk = []
                current_size = 0

        chunk.append(convo)
        current_size += size

    # Write any remaining conversations
    if chunk:
        out_path = os.path.join(OUTPUT_DIR, f"{CHUNK_PREFIX}{chunk_count:02}.json")
        with open(out_path, "w", encoding="utf-8") as f_out:
            json.dump(chunk, f_out, indent=2)
        print(f"✅ Wrote final chunk {chunk_count} ({len(chunk)} conversations) → {out_path}")

if __name__ == "__main__":
    main()
