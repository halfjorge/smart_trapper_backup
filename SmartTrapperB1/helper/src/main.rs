//! Smart Trapper helper (2026-10-26).
//!
//! A drop-in replacement for UXP_Trapper/real_bridge.py so the panel works on a computer without Python
//! (the co-worker's Mac). Same address (http://127.0.0.1:8765) and the same two requests:
//!   GET  /health -> {"ok":true, ..., "enginePath", "engineExists", "homeDir"}
//!   POST /run    -> runs the engine on the job folder the panel just exported, exactly like the bridge:
//!                   `smart_trapper_b1 <jobFolder> <trapPx>`, writes trapper_bridge_log.txt into the job
//!                   folder, answers {"ok": returncode==0 && traps.json exists, ...}.
//! It never changes how anything is trapped: it only starts the same engine program.
//!
//! The engine is looked for next to this program (smart_trapper_b1 / smart_trapper_b1.exe), or at
//! $SMART_TRAPPER_ENGINE. Options: --port N, --check (print health once and exit), --version.

use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

const VERSION: &str = env!("CARGO_PKG_VERSION");
static REQUESTS: AtomicU64 = AtomicU64::new(0);

fn now_iso() -> String {
    let d = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
    let secs = d.as_secs() as i64;
    let (days, rem) = (secs.div_euclid(86400), secs.rem_euclid(86400));
    // civil-from-days (Howard Hinnant), UTC
    let z = days + 719468;
    let era = z.div_euclid(146097);
    let doe = z - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let dd = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}.{:03}Z", y, m, dd, rem / 3600, (rem / 60) % 60, rem % 60, d.subsec_millis())
}

fn exe_dir() -> PathBuf {
    std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.to_path_buf())).unwrap_or_else(|| PathBuf::from("."))
}

fn engine_path() -> PathBuf {
    if let Ok(p) = std::env::var("SMART_TRAPPER_ENGINE") {
        if !p.trim().is_empty() { return PathBuf::from(p); }
    }
    let name = if cfg!(windows) { "smart_trapper_b1.exe" } else { "smart_trapper_b1" };
    exe_dir().join(name)
}

fn home_dir() -> String {
    std::env::var("HOME").or_else(|_| std::env::var("USERPROFILE")).unwrap_or_default()
}

fn log(event: &str, detail: &Value) {
    let path = exe_dir().join("helper.log");
    if let Ok(meta) = std::fs::metadata(&path) {
        if meta.len() > 5_000_000 { let _ = std::fs::remove_file(&path); }   // keep the log small
    }
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(&path) {
        let _ = writeln!(f, "{}", json!({"at": now_iso(), "event": event, "detail": detail}));
    }
}

fn health() -> Value {
    let e = engine_path();
    json!({
        "ok": true,
        "service": "smart-trapper-helper",
        "version": VERSION,
        "timestamp": now_iso(),
        "pid": std::process::id(),
        "requestCount": REQUESTS.load(Ordering::Relaxed),
        "enginePath": e.to_string_lossy(),
        "engineExists": e.exists(),
        "homeDir": home_dir(),
        "platform": std::env::consts::OS
    })
}

fn trap_px_of(v: Option<&Value>) -> i64 {
    match v {
        Some(Value::Number(n)) => n.as_f64().map(|f| f as i64).unwrap_or(5),
        Some(Value::String(s)) => s.trim().parse::<f64>().map(|f| f as i64).unwrap_or(5),
        _ => 5,
    }
}

fn str_of(v: Option<&Value>) -> String {
    v.and_then(|x| x.as_str()).unwrap_or("").to_string()
}

/// Same steps and answers as real_bridge.py run_engine().
fn run(payload: &Value) -> (u16, Value) {
    let n = REQUESTS.fetch_add(1, Ordering::Relaxed) + 1;
    let request_id = format!("{}-{:06}", SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs(), n);
    let settings = payload.get("settings").cloned().unwrap_or(json!({}));
    let mut job = str_of(settings.get("jobFolder"));
    if job.is_empty() { job = str_of(payload.get("jobFolder")); }
    let trap_px = trap_px_of(settings.get("trapPx"));
    log("run_requested", &json!({"requestId": request_id, "jobFolder": job, "trapPx": trap_px}));
    if job.is_empty() || job == "(none selected)" {
        return (400, json!({"ok": false, "message": "No job folder provided. Select an existing exported trap job folder in the panel first."}));
    }
    let engine = engine_path();
    if !engine.exists() {
        return (500, json!({"ok": false, "message": "Engine executable not found", "enginePath": engine.to_string_lossy()}));
    }
    let job_dir = PathBuf::from(&job);
    if !job_dir.exists() {
        return (500, json!({"ok": false, "message": "Job folder does not exist", "jobFolder": job}));
    }
    if !job_dir.join("job.json").exists() {
        return (500, json!({"ok": false, "message": "Job folder is missing job.json", "jobFolder": job}));
    }
    let started = Instant::now();
    let out = Command::new(&engine).arg(&job_dir).arg(trap_px.to_string())
        .current_dir(engine.parent().unwrap_or(Path::new("."))).output();
    let engine_ms = started.elapsed().as_millis() as u64;
    let (code, stdout, stderr) = match out {
        Ok(o) => (o.status.code().unwrap_or(-1), String::from_utf8_lossy(&o.stdout).to_string(), String::from_utf8_lossy(&o.stderr).to_string()),
        Err(e) => (-1, String::new(), format!("could not start the engine: {}", e)),
    };
    let traps = job_dir.join("traps.json");
    let mask_colors = job_dir.join("mask_colors.json");
    let mask_count = std::fs::read_to_string(&mask_colors).ok()
        .and_then(|t| serde_json::from_str::<Value>(&t).ok())
        .and_then(|v| v.as_object().map(|o| o.keys().filter(|k| !k.starts_with("__")).count()))
        .unwrap_or(0);
    let bridge_log = job_dir.join("trapper_bridge_log.txt");
    let log_payload = json!({
        "ranAt": now_iso(), "requestId": request_id, "helper": format!("smart_trapper_helper {}", VERSION),
        "pid": std::process::id(), "command": [engine.to_string_lossy(), job, trap_px.to_string()],
        "returncode": code, "engineMs": engine_ms, "stdout": stdout, "stderr": stderr,
        "maskColorCount": mask_count
    });
    let _ = std::fs::write(&bridge_log, serde_json::to_string_pretty(&log_payload).unwrap_or_default());
    let ok = code == 0 && traps.exists();
    log("run_completed", &json!({"requestId": request_id, "ok": ok, "returncode": code, "engineMs": engine_ms}));
    (if ok { 200 } else { 500 }, json!({
        "ok": ok,
        "message": if code == 0 { "Engine run complete" } else { "Engine run failed" },
        "requestId": request_id,
        "pid": std::process::id(),
        "jobFolder": job,
        "enginePath": engine.to_string_lossy(),
        "returncode": code,
        "engineMs": engine_ms,
        "bridgeTotalMs": engine_ms,
        "trapsJsonExists": traps.exists(),
        "trapsJson": traps.to_string_lossy(),
        "bridgeLog": bridge_log.to_string_lossy(),
        "maskColors": mask_colors.to_string_lossy(),
        "maskColorCount": mask_count
    }))
}

fn respond(stream: &mut TcpStream, status: u16, body: &Value) {
    let text = serde_json::to_string_pretty(body).unwrap_or_else(|_| "{}".into());
    let reason = match status { 200 => "OK", 400 => "Bad Request", 404 => "Not Found", _ => "Internal Server Error" };
    let head = format!("HTTP/1.1 {} {}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                       status, reason, text.len());
    let _ = stream.write_all(head.as_bytes());
    let _ = stream.write_all(text.as_bytes());
    let _ = stream.flush();
}

fn handle(mut stream: TcpStream) {
    let mut reader = BufReader::new(match stream.try_clone() { Ok(s) => s, Err(_) => return });
    let mut first = String::new();
    if reader.read_line(&mut first).is_err() { return; }
    let parts: Vec<&str> = first.split_whitespace().collect();
    if parts.len() < 2 { return; }
    let (method, path) = (parts[0].to_string(), parts[1].split('?').next().unwrap_or("").to_string());
    let mut length = 0usize;
    loop {
        let mut line = String::new();
        if reader.read_line(&mut line).is_err() || line == "\r\n" || line == "\n" || line.is_empty() { break; }
        if let Some((k, v)) = line.split_once(':') {
            if k.trim().eq_ignore_ascii_case("content-length") { length = v.trim().parse().unwrap_or(0); }
        }
    }
    match (method.as_str(), path.as_str()) {
        ("GET", "/health") => respond(&mut stream, 200, &health()),
        ("POST", "/run") => {
            let mut body = vec![0u8; length.min(50_000_000)];
            if reader.read_exact(&mut body).is_err() {
                respond(&mut stream, 400, &json!({"ok": false, "message": "Could not read the request"}));
                return;
            }
            let payload: Value = match serde_json::from_slice(if body.is_empty() { b"{}" } else { &body }) {
                Ok(v) => v,
                Err(e) => { respond(&mut stream, 400, &json!({"ok": false, "message": format!("Invalid JSON: {}", e)})); return; }
            };
            let (status, answer) = run(&payload);
            respond(&mut stream, status, &answer);
        }
        _ => respond(&mut stream, 404, &json!({"ok": false, "message": "Not found"})),
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--version") { println!("smart_trapper_helper {}", VERSION); return; }
    if args.iter().any(|a| a == "--check") { println!("{}", serde_json::to_string_pretty(&health()).unwrap()); return; }
    let port = args.iter().position(|a| a == "--port").and_then(|i| args.get(i + 1)).and_then(|p| p.parse::<u16>().ok()).unwrap_or(8765);
    let listener = match TcpListener::bind(("127.0.0.1", port)) {
        Ok(l) => l,
        Err(e) => {
            // Already running (another copy has the port): nothing to do.
            eprintln!("Smart Trapper helper: port {} is busy ({}). Is the helper already running?", port, e);
            log("port_busy", &json!({"port": port, "error": e.to_string()}));
            return;
        }
    };
    log("service_start", &json!({"port": port, "enginePath": engine_path().to_string_lossy(), "version": VERSION}));
    println!("Smart Trapper helper {} listening on http://127.0.0.1:{} (engine: {})", VERSION, port, engine_path().display());
    for stream in listener.incoming() {
        if let Ok(s) = stream { std::thread::spawn(move || handle(s)); }
    }
}
