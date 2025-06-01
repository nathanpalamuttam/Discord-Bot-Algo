# write_pipe.py
import os
import json

PIPE_PATH = "/tmp/trade_pipe"

def write_signal_to_pipe(data):
    try:
        with open(PIPE_PATH, 'w') as pipe:
            json.dump(data, pipe)
            pipe.write("\n")  # newline = message delimiter
        print(f"📤 Wrote signal to pipe: {data}")
    except Exception as e:
        print(f"❌ Error writing to pipe: {e}")
