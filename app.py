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
    html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CPU Stressor</title>
  <style>
    :root{
      --bg:#0b0f14;
      --panel:#0f1620;
      --panel2:#0c121a;
      --text:#dbe7ff;
      --muted:#8aa0c8;
      --border:rgba(255,255,255,.08);
      --accent:#7c5cff;
      --accent2:#22c55e;
      --danger:#ef4444;
      --warn:#f59e0b;
      --shadow: 0 10px 30px rgba(0,0,0,.45);
      --radius:16px;
    }
    *{ box-sizing:border-box; }
    body{
      margin:0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      background: radial-gradient(1200px 600px at 20% 0%, rgba(124,92,255,.18), transparent 60%),
                  radial-gradient(900px 500px at 90% 10%, rgba(34,197,94,.12), transparent 55%),
                  var(--bg);
      color:var(--text);
    }
    .wrap{ max-width: 980px; margin: 0 auto; padding: 28px 18px 60px; }
    header{ display:flex; align-items:flex-end; justify-content:space-between; gap:16px; margin-bottom: 18px; }
    h1{ font-size: 26px; margin:0; letter-spacing:.2px; }
    .sub{ color:var(--muted); margin-top:6px; font-size: 13px; line-height: 1.4; }
    .pill{
      display:inline-flex; align-items:center; gap:10px;
      padding:10px 12px; border:1px solid var(--border);
      background: rgba(255,255,255,.03); border-radius:999px;
      box-shadow: var(--shadow); color:var(--muted); font-size: 12px; white-space:nowrap;
    }
    .dot{ width:9px;height:9px;border-radius:99px; background: var(--warn); box-shadow: 0 0 0 3px rgba(245,158,11,.15); }
    .grid{ display:grid; grid-template-columns: 1.1fr .9fr; gap: 16px; margin-top: 16px; }
    @media (max-width: 860px){
      .grid{ grid-template-columns: 1fr; }
      header{ align-items:flex-start; flex-direction:column; }
      .pill{ width:fit-content; }
    }
    .card{
      border: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.02));
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow:hidden;
    }
    .card h2{
      margin:0; padding: 16px 16px 0;
      font-size: 14px; color: var(--muted);
      font-weight: 600; letter-spacing: .3px; text-transform: uppercase;
    }
    .card .content{ padding: 14px 16px 16px; }
    .row{ display:flex; gap: 12px; align-items:flex-end; flex-wrap:wrap; }
    label{ display:block; color:var(--muted); font-size: 12px; margin: 0 0 6px; }
    select, input{
      background: var(--panel2); color: var(--text);
      border: 1px solid var(--border); border-radius: 12px;
      padding: 10px 12px; outline: none; min-width: 160px;
    }
    input{ min-width: 200px; }
    select:focus, input:focus{
      border-color: rgba(124,92,255,.55);
      box-shadow: 0 0 0 4px rgba(124,92,255,.18);
    }
    .btn{
      border: 1px solid var(--border);
      background: rgba(255,255,255,.04);
      color: var(--text);
      padding: 10px 12px;
      border-radius: 12px;
      cursor: pointer;
      transition: transform .04s ease, background .15s ease, border-color .15s ease;
      user-select:none;
    }
    .btn:hover{ background: rgba(255,255,255,.07); border-color: rgba(255,255,255,.14); }
    .btn:active{ transform: translateY(1px); }
    .btn.primary{ background: linear-gradient(180deg, rgba(124,92,255,.35), rgba(124,92,255,.18)); border-color: rgba(124,92,255,.55); }
    .btn.good{ background: linear-gradient(180deg, rgba(34,197,94,.30), rgba(34,197,94,.14)); border-color: rgba(34,197,94,.55); }
    .btn.danger{ background: linear-gradient(180deg, rgba(239,68,68,.30), rgba(239,68,68,.14)); border-color: rgba(239,68,68,.55); }
    pre{
      margin:0; background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px; padding: 14px;
      color: #cfe0ff; overflow:auto;
      min-height: 140px; line-height: 1.45; font-size: 13px;
    }
    .kv{ display:grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
    .mini{ border:1px solid var(--border); background: rgba(255,255,255,.02); border-radius: 14px; padding: 12px; }
    .mini .k{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing:.3px; }
    .mini .v{ font-size: 16px; margin-top: 6px; }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <h1>CPU Stressor</h1>
        <div class="sub">Start/stop CPU load for testing. ALB health checks should hit <code>/health</code>.</div>
      </div>
      <div class="pill"><span class="dot" id="dot"></span><span id="pillText">Connecting…</span></div>
    </header>

    <div class="grid">
      <section class="card">
        <h2>Controls</h2>
        <div class="content">
          <div class="row">
            <div>
              <label for="workers">Workers</label>
              <select id="workers"></select>
            </div>
            <div>
              <label for="seconds">Seconds (1–600)</label>
              <input id="seconds" type="number" min="1" max="600" value="20" />
            </div>
            <button class="btn primary" onclick="start()">Start</button>
            <button class="btn danger" onclick="stop()">Stop</button>
          </div>

          <div style="height:12px"></div>

          <div class="row">
            <button class="btn good" onclick="health()">Health</button>
            <button class="btn" onclick="refresh()">Status</button>
          </div>

          <div class="kv">
            <div class="mini"><div class="k">Running</div><div class="v" id="running">—</div></div>
            <div class="mini"><div class="k">Remaining</div><div class="v" id="remaining">—</div></div>
            <div class="mini"><div class="k">Workers</div><div class="v" id="workersVal">—</div></div>
            <div class="mini"><div class="k">Host</div><div class="v" id="host">—</div></div>
          </div>
        </div>
      </section>

      <section class="card">
        <h2>Output</h2>
        <div class="content">
          <pre id="out">Loading…</pre>
        </div>
      </section>
    </div>
  </div>

<script>
function setPill(ok, text){
  const dot = document.getElementById('dot');
  dot.style.background = ok ? 'var(--accent2)' : 'var(--warn)';
  dot.style.boxShadow = ok ? '0 0 0 3px rgba(34,197,94,.15)' : '0 0 0 3px rgba(245,158,11,.15)';
  document.getElementById('pillText').textContent = text;
}
function fillWorkers() {
  const sel = document.getElementById('workers');
  sel.innerHTML = '';
  const max = 16;
  for (let i = 1; i <= max; i++) {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = i;
    sel.appendChild(opt);
  }
  sel.value = 2;
}
function parseStatus(txt){
  const lines = txt.trim().split('\\n');
  const kv = {};
  for (const line of lines){
    const [k, ...rest] = line.split('=');
    kv[k] = rest.join('=');
  }
  return kv;
}
function renderStatus(kv){
  document.getElementById('running').textContent = kv.running ?? '—';
  document.getElementById('remaining').textContent = ((kv.remaining_seconds ?? '—') + 's');
  document.getElementById('workersVal').textContent = kv.workers ?? '—';
  document.getElementById('host').textContent = kv.host ?? '—';
}
async function refresh(){
  try{
    const r = await fetch('/status', {cache:'no-store'});
    const t = await r.text();
    document.getElementById('out').textContent = t;
    const kv = parseStatus(t);
    renderStatus(kv);
    setPill(true, 'Connected');
  } catch(e){
    setPill(false, 'Disconnected');
    document.getElementById('out').textContent = String(e);
  }
}
async function health(){
  const r = await fetch('/health', {cache:'no-store'});
  const t = await r.text();
  document.getElementById('out').textContent = t;
  setPill(true, 'Health OK');
}
async function start(){
  const w = document.getElementById('workers').value;
  const s = document.getElementById('seconds').value;
  await fetch(`/stress?workers=${w}&seconds=${s}`, {cache:'no-store'});
  await refresh();
}
async function stop(){
  await fetch('/stop', {cache:'no-store'});
  await refresh();
}
fillWorkers();
setInterval(refresh, 1500);
refresh();
</script>
</body>
</html>
"""
    return html

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
