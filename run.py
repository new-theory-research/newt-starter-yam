"""
MA2-YAM cloud-validation demo — newt-starter-yam.

Sends mock observations (14D zero state + three 378x378 blank cameras) to
the deployed molmoact2-yam model and logs the (30, 14) action chunks that
come back. No robot hardware required.

Usage:
    uv sync
    export NT_API_KEY=<key>
    python run.py

Full runbook: README.md §Troubleshooting
"""

from __future__ import annotations

import os
import sys
import time

import newt

from embodiment import YamBimanual


def main() -> None:
    api_key = os.environ.get("NT_API_KEY")
    if not api_key:
        print(
            "Error: NT_API_KEY is not set.\n"
            "Export your API key before running:\n"
            "  export NT_API_KEY=<your-key>",
            file=sys.stderr,
        )
        sys.exit(1)

    rig = YamBimanual.from_config()

    robot = newt.Robot(
        api_key=api_key,
        model="molmoact2-yam",
        embodiment=rig,
    )

    print("Starting MA2-YAM mock inference loop…", flush=True)
    t_start = time.perf_counter()
    result = robot.run("pick up the object", max_duration=10.0)
    elapsed = time.perf_counter() - t_start

    print(
        f"\n=== MA2-YAM mock inference — done ===\n"
        f"model:          molmoact2-yam\n"
        f"stop_reason:    {result.stop_reason}\n"
        f"total_chunks:   {rig._chunks_received}\n"
        f"elapsed_s:      {elapsed:.1f}\n"
    )


if __name__ == "__main__":
    main()
