from http.server import HTTPServer, BaseHTTPRequestHandler
import threading, time, urllib.parse, os, socket

stop_event = threading.Event()
stress_running = False
stress_until = 0
stress_workers = 0
threads = []

def cpu_stress():
    while not stop_event.is_set():
        pass

def start_stress(workers: int, seconds: int):
    global stress_running, stress_until, stress_workers, threads
    stop_event.clear()
    threads = []
    for _ in range(workers):
        t = threading.Thread(target=cpu_stress, daemon=True)
        t.start()
        threads.append(t)
    stress_running = True
    stress_workers = workers
    stress_until = int(time.time()) + seconds

    def stopper():
        global stress_running
        time.sleep(seconds)
        stop_event.set()
        stress_running = False

    threading.Thread(target=stopper, daemon=True).start()

def stop_stress():
    global stress_running
    stop_event.set()
    stress_running = False

def status_text():
    now = int(time.time())
    remaining = max(0, stress_until - now) if stress_running else 0
    host = socket.gethostname()
    cpus = os.cpu_count() or 2
    return (
        f"host={host}\n"
        f"cpus={cpus}\n"
        f"running={stress_running}\n"
        f"workers={stress_workers if stress_running else 0}\n"
        f"remaining_seconds={remaining}\n"
    )

def page():
    # Simple HTML form UI with buttons (no need to type /health etc.)
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>CPU Stressor</title>
  <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; margin: 40px; max-width: 800px; }}
    .card {{ border: 1px solid #ddd; border-radius: 14px; padding: 18px; }}
    .row {{ display:flex; gap:12px; align-items:end; flex-wrap:wrap; }}
    label {{ display:block; margin: 10px 0 6px; }}
    input, select, button {{ font-size: 16px; padding: 8px 10px; }}
    button {{ cursor:pointer; }}
    pre {{ background:#f6f6f6; padding:12px; border-radius:10px; overflow:auto; }}
    .muted {{ color:#555; }}
  </style>
</head>
<body>
  <h1>CPU Stressor</h1>
  <p class="muted">Buttons for health/status and controls for stress. (Runs on this instance.)</p>

  <div class="card">
    <div class="row">
      <div>
        <label for="workers">Workers</label>
        <select id="workers"></select>
      </div>
      <div>
        <label for="seconds">Seconds</label>
        <input id="seconds" type="number" min="1" max="600" value="20" />
      </div>
      <div>
        <button onclick="start()">Start stress</button>
        <button onclick="stop()">Stop</button>
      </div>
      <div>
        <button onclick="health()">Health</button>
        <button onclick="refresh()">Status</button>
      </div>
    </div>

    <h3>Output</h3>
    <pre id="out">Loading…</pre>
  </div>

<script>
function fillWorkers() {{
  const sel = document.getElementById('workers');
  const max = 16; // UI max; server clamps to cpu_count
  for (let i=1; i<=max; i++) {{
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = i;
    sel.appendChild(opt);
  }}
  sel.value = 2;
}}

async function refresh() {{
  const r = await fetch('/status');
  document.getElementById('out').textContent = await r.text();
}}

async function health() {{
  const r = await fetch('/health');
  document.getElementById('out').textContent = await r.text();
}}

async function start() {{
  const w = document.getElementById('workers').value;
  const s = document.getElementById('seconds').value;
  await fetch(`/stress?workers=${{w}}&seconds=${{s}}`);
  await refresh();
}}

async function stop() {{
  await fetch('/stop');
  await refresh();
}}

fillWorkers();
setInterval(refresh, 1500);
refresh();
</script>

</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            return self._send(200, page().encode("utf-8"), "text/html; charset=utf-8")

        if path == "/health":
            return self._send(200, b"OK")

        if path == "/status":
            return self._send(200, status_text().encode("utf-8"))

        if path == "/stress":
            qs = urllib.parse.parse_qs(parsed.query)
            workers = int(qs.get("workers", [1])[0])
            seconds = int(qs.get("seconds", [10])[0])

            # clamp to safe limits
            cpus = os.cpu_count() or 2
            workers = max(1, min(workers, cpus))
            seconds = max(1, min(seconds, 600))

            stop_stress()
            start_stress(workers, seconds)
            return self._send(200, b"CPU stress started")

        if path == "/stop":
            stop_stress()
            return self._send(200, b"CPU stress stopped")

        return self._send(404, b"Not Found")

HTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
