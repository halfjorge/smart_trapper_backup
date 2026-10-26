# SmartTrapper Shared

This folder keeps the good settings for every job, so they don't get lost. That includes jobs Claude did by hand, outside the app.

## What's in here
| | What it is | Who changes it |
|---|---|---|
| `presets.json` | The settings for each kind of file (Standard, Geometric, Overlay, Tonal). The app's "What kind of file is this?" picker uses the same values. | **Only Sara** |
| `approved_runs/` | One small file per run that was judged. Each records the date, file, kind of job, every setting, the verdict (APPROVED / REJECTED / DELIVERED / REFERENCE) and a note. | Added after each judged run |
| `recipes/` | Plain-language "how it was made" cards, with exact commands, for anything done outside the app. | Claude, with every offline job |
| `runs_history_2026-10.csv` | Every October panel run and its settings (40 runs, 17 posters). Most have no verdict recorded. | Reference only |

## How to use it
1. Starting a job? Pick the matching kind of file in the panel. If unsure, look in `approved_runs/` for a similar poster.
2. Happy with a run? Add an entry to `approved_runs/` (soon this will be a button in the panel).
3. Want to change a preset? Sara edits `presets.json`. Nobody else does.

## Rule for every Claude chat working on the trapper
No delivery without a recipe card and an approved_runs entry:
- Every file Claude makes outside the app gets a card in `recipes/`, and a copy goes in that job's Trap Examples folder.
- Every file Claude delivers gets an entry in `approved_runs/` (verdict "DELIVERED" until Sara judges it).
- Never edit `presets.json` without Sara saying so.
- Only add new files here. Don't rewrite another chat's files.

Started 2026-10-26 (backfilled from the October runs and project notes).
