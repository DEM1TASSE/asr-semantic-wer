"""Yield the machine when its unified-memory pressure increases."""
import functools
import subprocess
import time

PAUSED = 75
SYSCTL = "/usr/sbin/sysctl"
MEMORY_PRESSURE = "/usr/bin/memory_pressure"


def pressure_level():
    return int(subprocess.check_output([SYSCTL, "-n", "kern.memorystatus_vm_pressure_level"]))


def free_percent():
    output = subprocess.check_output([MEMORY_PRESSURE, "-Q"], text=True)
    percent = output.rsplit("percentage:", 1)[1]
    return int(percent.strip().rstrip("%"))


@functools.cache
def configure_mlx(size):
    import mlx.core as mx

    check_memory()
    mx.set_cache_limit(64 * 1024**2)
    memory_mib = {"0.6b": 2304, "1.7b": 4608}[size]
    # MLX treats this as an allocator guideline. The OS pressure guard also
    # releases the model by exiting at the next utterance boundary.
    mx.set_memory_limit(memory_mib * 1024**2)


def check_memory():
    # Relaxed 2026-11-21: tolerate the "warn" level (2) that loading 1.7B triggers; stop only at critical (4).
    if pressure_level() >= 4:
        print("macOS memory pressure critical; stopping inference and releasing model memory.", flush=True)
        raise SystemExit(PAUSED)


def wait_for_headroom(minimum_free):
    consecutive = 0
    previous_state = None
    while consecutive < 3:
        level, free = pressure_level(), free_percent()
        ready = level <= 2 and free >= min(minimum_free, 30)
        if ready != previous_state:
            print(f"Memory pressure={level}, available={free}%; "
                  f"{'checking sustained headroom' if ready else 'waiting for normal pressure and free memory'}.",
                  flush=True)
            previous_state = ready
        consecutive = consecutive + 1 if ready else 0
        if consecutive < 3:
            time.sleep(15)
