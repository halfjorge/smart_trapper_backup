import json
import os
import platform
import subprocess
import traceback
import struct
import zlib
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TRAPPER_ROOT = ROOT.parent
RUN_LOG = ROOT / "real_bridge_last_run.json"
SERVICE_LOG = ROOT / "real_bridge_service.log"
HOST = "127.0.0.1"
PORT = 8765
BRIDGE_STARTED_AT = time.time()
BRIDGE_SESSION_ID = f"{int(BRIDGE_STARTED_AT)}-{uuid.uuid4().hex[:8]}"
REQUEST_COUNT = 0


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_service_log(event, payload=None):
    row = {
        "time": now_iso(),
        "sessionId": BRIDGE_SESSION_ID,
        "pid": os.getpid(),
        "event": event,
        "payload": payload or {}
    }
    try:
        with SERVICE_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def default_engine_path():
    exe = "smart_trapper_b1.exe" if platform.system().lower().startswith("win") else "smart_trapper_b1"
    return TRAPPER_ROOT / "SmartTrapperB1" / "engine" / "target" / "release" / exe


def write_run_snapshot(payload):
    RUN_LOG.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def build_health_payload():
    engine_path = default_engine_path()
    return {
        "ok": True,
        "service": "smart-trapper-real-bridge",
        "version": "0.1.0",
        "timestamp": now_iso(),
        "sessionId": BRIDGE_SESSION_ID,
        "pid": os.getpid(),
        "startedAt": datetime.fromtimestamp(BRIDGE_STARTED_AT, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "uptimeSec": round(max(0, time.time() - BRIDGE_STARTED_AT), 3),
        "requestCount": REQUEST_COUNT,
        "enginePath": str(engine_path),
        "engineExists": engine_path.exists(),
        "trapperRoot": str(TRAPPER_ROOT)
    }


def _paeth_predictor(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def sample_png_first_visible_rgb(path):
    path = Path(path)
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Not a PNG: {path}")

    pos = 8
    width = height = bit_depth = color_type = interlace = None
    idat_chunks = []

    while pos < len(data):
      if pos + 8 > len(data):
          break
      length = struct.unpack(">I", data[pos:pos + 4])[0]
      chunk_type = data[pos + 4:pos + 8]
      chunk_data = data[pos + 8:pos + 8 + length]
      pos += 12 + length

      if chunk_type == b"IHDR":
          width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", chunk_data)
      elif chunk_type == b"IDAT":
          idat_chunks.append(chunk_data)
      elif chunk_type == b"IEND":
          break

    if interlace not in (0, None):
        raise ValueError(f"Interlaced PNG not supported: {path}")
    if bit_depth == 8:
        bytes_per_sample = 1
    elif bit_depth == 16:
        bytes_per_sample = 2
    else:
        raise ValueError(f"Unsupported PNG bit depth {bit_depth}: {path}")

    if color_type == 6:
        channels = 4
    elif color_type == 2:
        channels = 3
    else:
        raise ValueError(f"Unsupported PNG color type {color_type}: {path}")

    bytes_per_pixel = channels * bytes_per_sample

    decompressed = zlib.decompress(b"".join(idat_chunks))
    stride = width * bytes_per_pixel
    out = bytearray(height * stride)

    src = 0
    for y in range(height):
        filter_type = decompressed[src]
        src += 1
        row = bytearray(decompressed[src:src + stride])
        src += stride

        if filter_type == 1:
            for i in range(stride):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                row[i] = (row[i] + left) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                up = out[(y - 1) * stride + i] if y > 0 else 0
                row[i] = (row[i] + up) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                up = out[(y - 1) * stride + i] if y > 0 else 0
                row[i] = (row[i] + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                left = row[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                up = out[(y - 1) * stride + i] if y > 0 else 0
                up_left = out[(y - 1) * stride + i - bytes_per_pixel] if (y > 0 and i >= bytes_per_pixel) else 0
                row[i] = (row[i] + _paeth_predictor(left, up, up_left)) & 0xFF
        elif filter_type != 0:
            raise ValueError(f"Unsupported PNG filter {filter_type}: {path}")

        out[y * stride:(y + 1) * stride] = row

    for y in range(height):
        row_start = y * stride
        for x in range(width):
            i = row_start + x * bytes_per_pixel
            if bit_depth == 8:
                r = out[i]
                g = out[i + 1]
                b = out[i + 2]
                a = out[i + 3] if channels == 4 else 255
            else:
                r = out[i]
                g = out[i + 2]
                b = out[i + 4]
                a = out[i + 6] if channels == 4 else 255
            if a > 0:
                return {"r": int(r), "g": int(g), "b": int(b), "a": int(a)}

    return None


def build_mask_color_map(job_folder, job_json_path):
    job = json.loads(job_json_path.read_text(encoding="utf-8"))
    out = {}
    for entry in job.get("files", []):
        if entry.get("kind") != "COLOR":
            continue
        png_rel = entry.get("png")
        name = entry.get("name")
        if not png_rel or not name:
            continue
        png_path = job_folder / png_rel
        if not png_path.exists():
            continue
        try:
            sampled = sample_png_first_visible_rgb(png_path)
        except Exception as exc:
            sampled = None
            out.setdefault("__errors__", {})[name] = str(exc)
        if sampled:
            out[name] = sampled
    return out


def run_engine(job_folder, trap_px, request_id=None):
    bridge_start = time.perf_counter()
    engine_path = default_engine_path()
    if not engine_path.exists():
        return {
            "ok": False,
            "message": "Engine executable not found",
            "enginePath": str(engine_path)
        }

    job_folder = Path(job_folder)
    if not job_folder.exists():
        return {
            "ok": False,
            "message": "Job folder does not exist",
            "jobFolder": str(job_folder)
        }

    job_json = job_folder / "job.json"
    if not job_json.exists():
        return {
            "ok": False,
            "message": "Job folder is missing job.json",
            "jobFolder": str(job_folder)
        }

    bridge_log = job_folder / "trapper_bridge_log.txt"
    mask_color_file = job_folder / "mask_colors.json"
    cmd = [str(engine_path), str(job_folder), str(int(trap_px))]
    engine_mtime = None
    try:
        if engine_path.exists():
            engine_mtime = datetime.fromtimestamp(engine_path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        engine_mtime = None

    engine_start = time.perf_counter()
    completed = subprocess.run(
        cmd,
        cwd=str(TRAPPER_ROOT),
        capture_output=True,
        text=True
    )
    engine_ms = round((time.perf_counter() - engine_start) * 1000)

    log_payload = {
        "ranAt": now_iso(),
        "requestId": request_id,
        "sessionId": BRIDGE_SESSION_ID,
        "pid": os.getpid(),
        "command": cmd,
        "engineMtimeUtc": engine_mtime,
        "returncode": completed.returncode,
        "engineMs": engine_ms,
        "stdout": completed.stdout,
        "stderr": completed.stderr
    }
    bridge_log.write_text(json.dumps(log_payload, indent=2), encoding="utf-8")

    try:
        mask_color_start = time.perf_counter()
        if mask_color_file.exists():
            mask_colors = json.loads(mask_color_file.read_text(encoding="utf-8"))
            real_color_count = len([k for k in mask_colors.keys() if not str(k).startswith("__")])
            if real_color_count == 0:
                mask_colors = build_mask_color_map(job_folder, job_json)
                mask_color_file.write_text(json.dumps(mask_colors, indent=2), encoding="utf-8")
        else:
            mask_colors = build_mask_color_map(job_folder, job_json)
            mask_color_file.write_text(json.dumps(mask_colors, indent=2), encoding="utf-8")
        mask_color_ms = round((time.perf_counter() - mask_color_start) * 1000)
    except Exception as exc:
        mask_colors = {}
        mask_color_ms = round((time.perf_counter() - mask_color_start) * 1000) if "mask_color_start" in locals() else None
        log_payload["maskColorError"] = str(exc)
        bridge_log.write_text(json.dumps(log_payload, indent=2), encoding="utf-8")

    traps_json = job_folder / "traps.json"
    bridge_total_ms = round((time.perf_counter() - bridge_start) * 1000)
    log_payload["maskColorMs"] = mask_color_ms
    log_payload["bridgeTotalMs"] = bridge_total_ms
    bridge_log.write_text(json.dumps(log_payload, indent=2), encoding="utf-8")

    return {
        "ok": completed.returncode == 0 and traps_json.exists(),
        "message": "Engine run complete" if completed.returncode == 0 else "Engine run failed",
        "requestId": request_id,
        "sessionId": BRIDGE_SESSION_ID,
        "pid": os.getpid(),
        "jobFolder": str(job_folder),
        "enginePath": str(engine_path),
        "returncode": completed.returncode,
        "engineMs": engine_ms,
        "maskColorMs": mask_color_ms,
        "bridgeTotalMs": bridge_total_ms,
        "trapsJsonExists": traps_json.exists(),
        "trapsJson": str(traps_json),
        "bridgeLog": str(bridge_log),
        "maskColors": str(mask_color_file),
        "maskColorCount": len([k for k in mask_colors.keys() if not str(k).startswith("__")])
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            json_response(self, 200, build_health_payload())
            return
        json_response(self, 404, {"ok": False, "message": "Not found"})

    def do_POST(self):
        global REQUEST_COUNT
        if self.path != "/run":
            json_response(self, 404, {"ok": False, "message": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            json_response(self, 400, {"ok": False, "message": f"Invalid JSON: {exc}"})
            return

        snapshot = {
            "receivedAt": now_iso(),
            "sessionId": BRIDGE_SESSION_ID,
            "pid": os.getpid(),
            "payload": payload
        }
        write_run_snapshot(snapshot)

        try:
            REQUEST_COUNT += 1
            request_id = f"{int(time.time())}-{REQUEST_COUNT:06d}"
            settings = payload.get("settings", {}) or {}
            job_folder = settings.get("jobFolder") or payload.get("jobFolder")
            trap_px = settings.get("trapPx", 5)
            append_service_log("run_requested", {
                "requestId": request_id,
                "jobFolder": job_folder,
                "trapPx": trap_px
            })

            if not job_folder or job_folder == "(none selected)":
                json_response(self, 400, {
                    "ok": False,
                    "message": "No job folder provided. Select an existing exported trap job folder in the panel first.",
                    "savedTo": str(RUN_LOG)
                })
                append_service_log("run_rejected_missing_job_folder", {"requestId": request_id})
                return

            result = run_engine(job_folder, trap_px, request_id=request_id)
            result["savedTo"] = str(RUN_LOG)
            append_service_log("run_completed", {
                "requestId": request_id,
                "ok": bool(result.get("ok")),
                "returncode": result.get("returncode"),
                "engineMs": result.get("engineMs"),
                "bridgeTotalMs": result.get("bridgeTotalMs")
            })
            json_response(self, 200 if result.get("ok") else 500, result)
        except Exception as exc:
            append_service_log("run_exception", {
                "message": str(exc),
                "traceback": traceback.format_exc()
            })
            json_response(self, 500, {
                "ok": False,
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "sessionId": BRIDGE_SESSION_ID,
                "pid": os.getpid(),
                "savedTo": str(RUN_LOG)
            })


if __name__ == "__main__":
    append_service_log("service_start", {
        "host": HOST,
        "port": PORT,
        "trapperRoot": str(TRAPPER_ROOT),
        "enginePath": str(default_engine_path())
    })
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Smart Trapper real bridge listening on http://{HOST}:{PORT} session={BRIDGE_SESSION_ID} pid={os.getpid()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        append_service_log("service_stop", {})
        server.server_close()
