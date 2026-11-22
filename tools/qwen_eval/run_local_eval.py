"""Resume this evaluation in serial, releasing model memory above normal pressure."""
import os
import subprocess
import sys
import time
from pathlib import Path

from local_memory import PAUSED, wait_for_headroom

ROOT = Path(__file__).resolve().parent
STUDENT = Path.home() / "semwer-local-cpu"
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "mlx-audio-src"), "HF_HUB_OFFLINE": "1"}
STAGES = [
    (55, sys.executable, "transcribe.py", "--size", "1.7b", "--protected"),
    (40, sys.executable, "evaluate_asr.py", "--include-1.7b"),
    (45, str(STUDENT / ".venv/bin/python"), "score_student.py", "five_systems"),
]


def main():
    for minimum_free, python, script, *args in STAGES:
        while True:
            print(f"Stage: {script} {' '.join(args)}", flush=True)
            wait_for_headroom(minimum_free)
            result = subprocess.run(
                ["/usr/bin/caffeinate", "-i", "/usr/bin/nice", "-n", "15", python, "-u", script, *args],
                cwd=ROOT, env=ENV,
            )
            if result.returncode == PAUSED:
                print("Memory guard paused the stage; trying again after a cooldown.", flush=True)
                time.sleep(180)
                continue
            result.check_returncode()
            break
    print("Local AMI evaluation complete (LibriSpeech stages removed).", flush=True)


if __name__ == "__main__":
    main()
