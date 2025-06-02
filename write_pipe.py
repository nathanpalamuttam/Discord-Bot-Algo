# write_pipe.py
import os
import json

PIPE_PATH = "/tmp/trade_pipe"

def write_signal_to_pipe(data):
    if not os.path.exists(PIPE_PATH):
        os.mkfifo(PIPE_PATH)

    try:
        # Open in non-blocking mode from the start
        fd = os.open(PIPE_PATH, os.O_WRONLY | os.O_NONBLOCK)
        with os.fdopen(fd, 'w', buffering=1) as pipe:
            json.dump(data, pipe)
            pipe.write("\n")
        print(f"📤 Wrote signal to pipe: {data}")
    except OSError as e:
        if e.errno == 6:  # ENXIO - No such device or address (no reader)
            print("❌ No reader connected to pipe — skipping write.")
        else:
            print(f"❌ Error opening/writing to pipe: {e}")
    except BrokenPipeError:
        print("❌ No reader connected to pipe — skipping write.")
    except Exception as e:
        print(f"❌ Error writing to pipe: {e}")