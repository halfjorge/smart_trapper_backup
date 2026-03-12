# Smart Trapper Bridge Contract

The UXP panel is designed to talk to a local bridge service over HTTP on `localhost`.

## Why this exists

The current ExtendScript pipeline launches the Rust engine directly as an external process. A UXP plugin does not map cleanly to that same `exe + args + wait for files` flow, so a companion bridge is the cleanest replacement.

## Proposed endpoints

### `GET /health`

Response:

```json
{
  "ok": true,
  "service": "smart-trapper-bridge",
  "version": "0.1.0"
}
```

### `POST /run`

Request:

```json
{
  "generatedAt": "2026-03-11T15:00:00.000Z",
  "settings": {
    "fullDebug": false,
    "cutTopKey": true,
    "preflightCleanup": true,
    "alphaThreshold": 8,
    "edgeBiasPx": 0,
    "trapPx": 5,
    "mode": "auto",
    "bridgeUrl": "http://127.0.0.1:8765",
    "jobFolder": "C:/path/to/existing/exported/job"
  },
  "document": {
    "title": "Example.psd",
    "mode": "rgb",
    "width": 3304,
    "height": 2821,
    "resolution": 300
  }
}
```

Response:

```json
{
  "ok": false,
  "message": "Bridge not implemented yet"
}
```

## Expected future responsibilities of the bridge

- accept run requests from the UXP panel
- coordinate the external Rust engine
- manage temporary job folders
- return structured progress and errors
- eventually support polling or streamed status

## Proposed next implementation step

Add a small local bridge executable that exposes:

- `GET /health`
- `POST /run`

and internally shells out to the existing Rust trapper binary with the same job-folder contract used today.

## Implemented first real step

The current `real_bridge.py` already supports:

- `GET /health`
- `POST /run`

and can run the existing Rust engine against an already-exported job folder that contains `job.json`.
