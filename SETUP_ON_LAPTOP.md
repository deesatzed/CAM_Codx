# Setting Up CAM on Your Laptop — Beginner's Guide

**For:** someone who has never installed CAM before and wants a working copy on a laptop.
**Written:** 2026-07-04
**Reading level:** assumes you can open a Terminal and copy-paste. No prior CAM knowledge needed.

---

## The big picture (read this first)

CAM is made of **two GitHub repositories** plus **two things that do NOT live on GitHub**:

| Piece | What it is | How you get it |
|---|---|---|
| **CAM_CAM** | The engine — the actual `cam` program and its brain-reading code | `git clone` from GitHub |
| **CAM_Codx** | The "program manager" — goals, docs, registries that organize CAM work | `git clone` from GitHub |
| **`claw.db`** | The **brain** — 2,474 learned methodologies. ~117 MB. | **You copy it by hand** (it is NOT on GitHub) |
| **`.env`** | Your **secret API keys** (OpenRouter, etc.) | **You copy or recreate it by hand** (it is NOT on GitHub) |

> **Why aren't `claw.db` and `.env` on GitHub?**
> They are deliberately excluded (`.gitignore`). `claw.db` is a big binary that changes every
> run — Git would choke on it. `.env` holds secret keys that must never be published. So
> `git clone` gives you the *code*, and you supply the *brain* and the *keys* separately.

**End goal:** on your laptop you will have a folder you can `cd` into and run `cam`, and it will
answer using the same 2,474-methodology brain you have on the main machine.

---

## What you need before you start

1. **A Mac or Linux laptop** with a Terminal. (Windows works via WSL, not covered here.)
2. **Python 3.12 or newer.** Check with:
   ```bash
   python3 --version
   ```
   If it says 3.12 or higher, you're good. If not, install Python 3.12+ first
   (e.g. from python.org or `brew install python@3.12` on a Mac).
3. **Git.** Check with `git --version`. If missing, install it (`brew install git` on a Mac).
4. **An OpenRouter API key.** CAM uses this to talk to the AI models. Get one at
   https://openrouter.ai (you fund it with a small balance). Copy the key somewhere safe —
   you'll paste it in Step 5.
5. **A way to move ~120 MB of files** from the main machine to the laptop: AirDrop, a USB drive,
   `scp` over the network, or a cloud folder (Dropbox/Drive). You'll use this in Step 4.

---

## Step 1 — Pick a home folder on the laptop

Open Terminal and make one parent folder to keep both repos together:

```bash
mkdir -p ~/CAM
cd ~/CAM
```

Everything below happens inside `~/CAM`. (You can pick any folder — just be consistent.)

---

## Step 2 — Download the two repositories

```bash
cd ~/CAM
git clone https://github.com/deesatzed/CAM_CAM.git
git clone https://github.com/deesatzed/CAM_Codx.git
```

You now have `~/CAM/CAM_CAM` (the engine) and `~/CAM/CAM_Codx` (the program manager).

> If Git asks for a username/password, you may need a GitHub Personal Access Token, or use SSH
> URLs (`git@github.com:...`). Ask whoever owns the repos for access if the clone fails.

---

## Step 3 — Install the engine (create its Python environment)

A "virtual environment" (venv) is a private Python sandbox for CAM so it doesn't disturb the
rest of your laptop.

```bash
cd ~/CAM/CAM_CAM
python3 -m venv .venv
source .venv/bin/activate        # turns the sandbox ON — your prompt now shows (.venv)
pip install -e ".[dev]"          # installs CAM and everything it needs (takes a few minutes)
```

Test that the `cam` command exists:

```bash
cam --help
```

You should see a list of commands (`mine`, `enrich`, `enhance`, `status`, ...). If you do, the
engine is installed.

> **Remember this:** every new Terminal session, before using `cam`, run
> `source ~/CAM/CAM_CAM/.venv/bin/activate` first. If `cam` ever says "command not found," the
> sandbox is probably just turned off — run that line again.

---

## Step 4 — Copy the brain (`claw.db`) and the config files

This is the part `git clone` could not do. On the **main machine**, these files live in the run
folder `repo622sn/CAM_CAM`:

- `claw.db` ................ the brain (~117 MB) — **required**
- `claw.toml` .............. the main config (which models, which DB) — **required**
- `claw_cheap.toml`, `claw_dspro.toml`, `claw_grok.toml` ... alternate model profiles — optional
- `.env` .................. your secret keys — copy it if you want the exact same keys, or
  recreate it in Step 5

**Copy them into `~/CAM/CAM_CAM` on the laptop** — the same folder that has `src/`, `README.md`,
etc. Put `claw.db` at the top level of that folder (next to `claw.toml`), because the config's
`db_path = "claw.db"` looks for it right there.

Pick whichever transfer method you have:

- **AirDrop (Mac-to-Mac):** on the main machine, select the files, AirDrop them, then move them
  into `~/CAM/CAM_CAM` on the laptop.
- **USB drive:** copy the files onto the drive, plug into the laptop, drag them into
  `~/CAM/CAM_CAM`.
- **`scp` over the network** (if you know the main machine's address):
  ```bash
  # run this ON THE LAPTOP; replace user@main-machine and the path
  scp user@main-machine:/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db      ~/CAM/CAM_CAM/
  scp user@main-machine:/Volumes/WS4TB/repo622sn/CAM_CAM/claw.toml    ~/CAM/CAM_CAM/
  scp user@main-machine:/Volumes/WS4TB/repo622sn/CAM_CAM/claw_*.toml  ~/CAM/CAM_CAM/
  ```

Confirm the brain landed in the right place and is the full size:

```bash
cd ~/CAM/CAM_CAM
ls -lh claw.db          # should show ~117M, not a few KB
```

If it shows only a few kilobytes, the copy didn't finish — redo it.

---

## Step 5 — Set up your API keys (`.env`)

If you copied `.env` in Step 4, you can skip to Step 6. Otherwise create one from the template:

```bash
cd ~/CAM/CAM_CAM
cp .env.example .env
```

Open `.env` in any text editor and fill in your real key(s). At minimum:

```
OPENROUTER_API_KEY=sk-or-...your-real-key...
```

The template also lists optional keys (`XAI_API_KEY`, `GOOGLE_API_KEY`) and model names — you
can leave those as-is to start. **Never commit `.env` to Git or share it** — it's your secret.

---

## Step 6 — Prove it works

Run these from inside `~/CAM/CAM_CAM` with the venv active:

```bash
cd ~/CAM/CAM_CAM
source .venv/bin/activate      # if not already active

cam status                     # should report the system is up
cam stats                      # should show ~2474 methodologies — that means the brain loaded
```

If `cam stats` shows roughly **2,474 methodologies**, you have successfully copied the brain and
the laptop is running the *same* CAM knowledge as the main machine. 🎉

---

## Step 7 — Create the Codex-safe CAM wrapper

Codex may run in a sandbox that can read your CAM files but cannot write SQLite
sidecar files beside `claw.db`. Do not fix that by granting broad shell or
folder access. Instead, create one narrow wrapper command that pins the CAM
runtime, brain, config, and `.env`.

Run this from the CAM_Codx checkout:

```bash
cd ~/CAM/CAM_Codx
python tools/cam_setup_wizard.py \
  --cam-home ~/CAM \
  --skip-clone \
  --install-codex-skill \
  --non-interactive
```

The wizard writes:

```text
~/CAM/scripts/cam-codx
~/.codex/skills/cam-codx-setup/SKILL.md
```

Use that wrapper when Codex needs CAM:

```bash
~/CAM/scripts/cam-codx status
~/CAM/scripts/cam-codx stats
```

When Codex asks for permission, approve only this narrow command prefix:

```text
~/CAM/scripts/cam-codx
```

That lets CAM update your local `claw.db` and SQLite sidecar files without
giving Codex arbitrary write access outside the project.

Now start Codex inside the repo you want CAM to help with:

```bash
cd /path/to/your/project
codex
```

Inside Codex, say:

```text
Use cam-codx-setup to verify CAM.
```

---

## The one rule that avoids all confusion

CAM finds its config and brain **relative to the folder you are standing in** when you run it.
So always run CAM the same way:

```bash
cd ~/CAM/CAM_CAM        # stand in the run folder
source .venv/bin/activate
cam <command>
```

If you run `cam` from some other folder, it won't find `claw.toml`/`claw.db` and will act like
it has an empty brain. That's the #1 beginner surprise. Stand in `~/CAM/CAM_CAM`.

When you are inside Codex, prefer the wrapper:

```bash
~/CAM/scripts/cam-codx <command>
```

> **Advanced/optional:** you can force a specific brain file regardless of folder by setting
> `export CLAW_DB_PATH=/full/path/to/claw.db` before running `cam`. Beginners can ignore this.

---

## Common problems and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `cam: command not found` | venv not active | `source ~/CAM/CAM_CAM/.venv/bin/activate` |
| `cam stats` shows 0 methodologies | `claw.db` missing or in wrong folder | Put `claw.db` in `~/CAM/CAM_CAM/` next to `claw.toml`; check `ls -lh claw.db` |
| Codex says CAM files are readable but not writable | CAM lives outside the active Codex workspace | Use `~/CAM/scripts/cam-codx` and approve that exact prefix |
| Errors mentioning API key / 401 | `.env` missing or key wrong | Redo Step 5; verify the OpenRouter key is valid and funded |
| `claw.db` copied but only a few KB | transfer was interrupted | Copy it again; confirm ~117M |
| `pip install` fails on Python version | Python older than 3.12 | Install Python 3.12+, recreate the venv |
| Git clone asks for password and fails | need GitHub access | Get repo access / a Personal Access Token from the owner |

---

## Quick reference card

```bash
# One-time setup
mkdir -p ~/CAM && cd ~/CAM
git clone https://github.com/deesatzed/CAM_CAM.git
git clone https://github.com/deesatzed/CAM_Codx.git
cd ~/CAM/CAM_CAM
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# ...then copy claw.db + claw.toml (+ .env) into ~/CAM/CAM_CAM ...
cp .env.example .env        # if you didn't copy .env; then edit in your OpenRouter key

# Every time you use CAM afterwards
cd ~/CAM/CAM_CAM
source .venv/bin/activate
cam stats                   # sanity check: ~2474 methodologies
cam <command>

# One-time Codex wrapper setup
cd ~/CAM/CAM_Codx
python tools/cam_setup_wizard.py --cam-home ~/CAM --skip-clone \
  --install-codex-skill \
  --non-interactive
~/CAM/scripts/cam-codx stats
```

---

## What "authoritative" means (so you keep them in sync)

The main machine is the source of truth (see `DB_REGISTRY.md`). Your laptop copy is a **working
duplicate**. If you mine or enrich on the laptop, its `claw.db` will drift from the main one —
that's expected. To re-sync, copy the newer `claw.db` over the older one (whichever machine did
the latest mining). The registry records which is current.
