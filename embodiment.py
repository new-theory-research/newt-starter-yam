"""
MA2-YAM embodiment — YamBimanual.

Implements the newt Embodiment protocol for the MA2-YAM bimanual rig:
  read_state()      → 14D zero state + three 378×378 blank cameras
  execute(chunk)    → logs the (30, 14) action chunk

This is the mock (cloud-validation) implementation. Swap read_state and
execute for real hardware callbacks when you wire the i2rt driver and
cameras. The class shape and from_config() convention stay identical —
only the method bodies change.

Wire contract (MA2-YAM):
  state:  shape (14,), dtype float32  — left arm joints 0–6, right arm 7–13
  images: top_cam / left_cam / right_cam, each (3, 378, 378) uint8 CHW
  chunk:  shape (30, 14)

Camera order is fixed — mismatch closes the connection with error 4422.
Source: apps/docs/content/docs/models/molmoact2/yam.mdx
"""
from __future__ import annotations

import numpy as np

# Camera order is fixed — load-bearing for the visual encoder.
# Source: apps/docs/content/docs/models/molmoact2/yam.mdx
_CAMERA_KEYS = ["top_cam", "left_cam", "right_cam"]


class YamBimanual:
    """Mock MA2-YAM embodiment.

    Implements the newt Embodiment protocol: read_state() and execute().
    No hardware dependencies — returns zero state and blank cameras.

    Usage::

        from embodiment import YamBimanual
        robot = newt.Robot(embodiment=YamBimanual.from_config())
        result = robot.run("pick up the object", max_duration=10.0)
    """

    def __init__(self) -> None:
        self._chunks_received: int = 0

    @classmethod
    def from_config(cls) -> "YamBimanual":
        """Construct from site config.

        The mock implementation requires no hardware config — returns a
        fresh instance. When you wire real hardware, this classmethod reads
        ~/.config/nt/nt.toml for arm IPs, camera serials, and extrinsics.
        """
        return cls()

    def read_state(self) -> dict:
        """Return one observation frame.

        Returns 14D zero state (left arm 0-6, right arm 7-13) and three
        378x378 blank cameras in fixed order (top=overhead, left/right=wrist).
        """
        return {
            "state": np.zeros(14, dtype=np.float32),
            "images": {
                cam: np.zeros((3, 378, 378), dtype=np.uint8) for cam in _CAMERA_KEYS
            },
        }

    def execute(self, chunk: np.ndarray) -> None:
        """Apply one action chunk.

        Args:
            chunk: Shape (30, 14) float32 — 30-step horizon, 14 bimanual joints.
        """
        self._chunks_received += 1
        print(
            f"chunk {self._chunks_received:3d}: shape={chunk.shape}  "
            f"first_row={chunk[0].tolist()}",
            flush=True,
        )
