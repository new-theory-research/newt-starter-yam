# newt-starter-yam

A minimal starter kit for validating MA2-YAM cloud inference end-to-end. No robot hardware required — mock callbacks send zero-state observations to the deployed `molmoact2-yam` model and log the (30, 14) action chunks that come back.

## TL;DR

This kit validates the MA2-YAM cloud inference loop with mock callbacks. Real hardware wiring is your responsibility; this starter intentionally has no hardware deps.

```bash
gh repo clone new-theory-research/newt-starter-yam
cd newt-starter-yam
uv sync
export NT_API_KEY=your_key_here
python run.py
```

## Prerequisites

- **NT API key** — set as `NT_API_KEY` in your environment
- **SSH key registered** with the `new-theory-research` GitHub org — required for `uv sync` to resolve the private `newt` SDK dep
- **Python 3.11–3.13** and [uv](https://docs.astral.sh/uv/getting-started/installation/) installed (a `.python-version` file pins 3.12 — uv handles this automatically)

### No SSH key?

If your machine authenticates to GitHub over HTTPS only (e.g. via `gh auth`), `uv sync` will fail because the deps use `git+ssh://`. Two commands rewrite those URLs to HTTPS:

```bash
gh auth setup-git
git config --global url."https://github.com/".insteadOf "ssh://git@github.com/"
```

`gh auth setup-git` registers the GitHub CLI as your HTTPS credential helper. The `insteadOf` line rewrites the `ssh://git@github.com/` prefix that uv passes to git for every `git+ssh://git@github.com/...` dep. After both commands, `uv sync` resolves via HTTPS and authenticates with your existing `gh` session.

## Setup

**1. Clone the repo**

```bash
gh repo clone new-theory-research/newt-starter-yam
cd newt-starter-yam
```

**2. Install dependencies**

```bash
uv sync
```

Resolves `newt` (the New Theory SDK) and `numpy`. No hardware drivers.

**3. Set your API key**

```bash
export NT_API_KEY=your_key_here
```

**4. Run**

```bash
python run.py
```

## What success looks like

The first call cold-starts the inference container — expect a 60–90 second pause with a `ColdStartRetry` warning printed before the first chunk arrives. This is normal.

Once the container is warm, each inference call returns a (30, 14) action chunk within a few seconds. The loop terminates when `max_duration` elapses.

Expected output:

```
Starting MA2-YAM mock inference loop…
chunk   1: shape=(30, 14)  first_row=[...]
chunk   2: shape=(30, 14)  first_row=[...]
...

=== MA2-YAM mock inference — done ===
model:          molmoact2-yam
stop_reason:    max_duration
total_chunks:   N
elapsed_s:      10.x
```

## Troubleshooting

**`uv sync` fails with authentication errors**

Test SSH access before syncing: `ssh -T git@github.com` should print `Hi <username>! You've successfully authenticated`. If it fails, your key isn't registered with the `new-theory-research` org — verify the key is listed under your GitHub account settings and ask your New Theory contact to add you to the org.

**Confusing 4404 errors on startup**

A stale `NT_INFERENCE_URL` environment variable pins routing to the wrong inference app. Unset it:

```bash
unset NT_INFERENCE_URL
python run.py
```

**`ServerError` with an unhelpful message**

Check `e.envelope.context.error_type`, not just `str(e)`. The structured field names the root cause; the string representation is a summary.

**Error 4422 — wrong input shape**

The MA2-YAM contract requires:
- `state`: shape `(14,)`, dtype `float32`
- Each camera: shape `(3, 378, 378)`, dtype `uint8`
- Camera keys in order: `top_cam`, `left_cam`, `right_cam`

A mismatch returns 4422 with `expected_shape` and `got_shape` in the envelope. Check `e.envelope.context`.

**First call hangs for 60–90 seconds then times out**

The inference container is cold-starting. `ColdStartRetry` handles the retry automatically. If the second call also fails, check your `NT_API_KEY` and network access.

**`NT_API_KEY` error on startup**

`run.py` exits immediately if `NT_API_KEY` is not set. Set it in the same shell session:

```bash
export NT_API_KEY=your_key_here
python run.py
```

## Your embodiment class

`embodiment.py` exports `YamBimanual` — the mock implementation of the newt Embodiment protocol. It lives in your repo, not the SDK:

```python
from embodiment import YamBimanual
robot = newt.Robot(embodiment=YamBimanual.from_config())
```

`YamBimanual` implements two methods the SDK calls: `read_state()` returns a zero-state observation dict, and `execute(chunk)` logs the incoming action chunk. `from_config()` is where hardware initialization goes — the mock version just returns a new instance.

When you wire real hardware, swap the method bodies. The class shape, the `from_config()` classmethod, and the import line in `run.py` stay identical.

## Wiring real hardware

MA2-YAM hardware integration (i2rt drivers, joint mapping, gripper polarity) is bring-your-own. This starter validates the cloud contract end-to-end — swap the `read_state` and `execute` implementations in `YamBimanual` (in `embodiment.py`) for real hardware callbacks when you have hardware.

The MA2-YAM model uses a 14D bimanual joint state: left arm joints 0–6, right arm joints 7–13, gripper-last in each half. Cameras are `top_cam` (overhead), `left_cam` (left wrist), `right_cam` (right wrist) — the order is fixed and must match the trained contract.

See the [MA2-YAM model page](https://github.com/new-theory-research/portal/blob/main/apps/docs/content/docs/models/molmoact2/yam.mdx) for the full joint layout and camera role documentation.

## What's next

- [MA2-YAM model page](https://github.com/new-theory-research/portal/blob/main/apps/docs/content/docs/models/molmoact2/yam.mdx) — contract reference: joint layout, camera roles, image shape, action shape
- YAM bimanual tutorial — step-by-step hardware integration guide (coming soon)
- Error catalog — full list of NT API error codes and envelope fields (coming soon)
