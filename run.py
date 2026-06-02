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

import numpy as np

import newt

# Camera order is fixed — mismatch closes the connection with error 4422.
# Source: apps/docs/content/docs/models/molmoact2/yam.mdx
_CAMERA_KEYS = ["top_cam", "left_cam", "right_cam"]


def read_state() -> dict:
    """Mock read_state callback.

    Returns 14D zero state (left arm 0-6, right arm 7-13) and three
    378x378 blank cameras in fixed order (top=overhead, left/right=wrist).
    """
    return {
        "state": np.zeros(14, dtype=np.float32),
        "images": {
            cam: np.zeros((3, 378, 378), dtype=np.uint8) for cam in _CAMERA_KEYS
        },
    }


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

    chunks_received: list[np.ndarray] = []

    def execute(chunk: np.ndarray) -> None:
        chunks_received.append(chunk)
        print(
            f"chunk {len(chunks_received):3d}: shape={chunk.shape}  "
            f"first_row={chunk[0].tolist()}",
            flush=True,
        )

    robot = newt.Robot(
        api_key=api_key,
        model="molmoact2-yam",
        read_state=read_state,
        execute=execute,
    )

    print("Starting MA2-YAM mock inference loop…", flush=True)
    t_start = time.perf_counter()
    result = robot.run("pick up the object", max_duration=10.0)
    elapsed = time.perf_counter() - t_start

    print(
        f"\n=== MA2-YAM mock inference — done ===\n"
        f"model:          molmoact2-yam\n"
        f"stop_reason:    {result.stop_reason}\n"
        f"total_chunks:   {len(chunks_received)}\n"
        f"elapsed_s:      {elapsed:.1f}\n"
    )


if __name__ == "__main__":
    main()
