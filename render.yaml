# Transformer Health Control Room — Cloud Deployment (Render)

This gives you ONE permanent link, e.g.:
`https://transformer-control-room.onrender.com`

Anyone — the control room incharge, your review panel, anyone — just opens
that link in any browser, on any device. No laptop running, no Colab, no
cells, nothing. The dashboard auto-refreshes every 30 seconds on its own.

## What's in this folder

```
cloud_deploy/
├── app.py                  <- the whole server: listener + model + dashboard
├── templates/
│   └── dashboard.html      <- the page people actually see
├── models/                 <- your 4 trained .pkl files (already included)
├── simulate_esp32.py       <- run on YOUR laptop to test, before hardware exists
├── requirements.txt
└── render.yaml             <- tells Render how to run this
```

## One-time deployment steps (15–20 minutes, do this once)

### Step 1 — Put this code on GitHub
1. Go to github.com, sign in (create a free account if you don't have one)
2. Click **New repository** → name it e.g. `transformer-control-room` → set to **Public** → Create
3. On the new repo page, click **uploading an existing file**
4. Drag in ALL the files and folders from this `cloud_deploy` folder (app.py, templates/, models/, requirements.txt, render.yaml, simulate_esp32.py)
5. Click **Commit changes**

### Step 2 — Deploy on Render
1. Go to **render.com** → sign up free (you can sign up with your GitHub account directly — easiest option)
2. Click **New +** → **Web Service**
3. Connect your GitHub account if asked, then select your `transformer-control-room` repository
4. Render will likely auto-detect the `render.yaml` file and pre-fill everything. If not, fill manually:
   - **Name:** transformer-control-room
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - **Instance Type:** Free
5. Click **Create Web Service**
6. Wait 3–5 minutes while it builds (you'll see logs scrolling)
7. When done, Render shows your live URL at the top, like:
   `https://transformer-control-room.onrender.com`

That's it. That URL is permanent. Bookmark it, share it, put it in your PPT.

## Testing it before hardware arrives

On YOUR laptop (just for testing, not needed after hardware is connected):

1. Open Command Prompt in this folder
2. Run: `pip install paho-mqtt`
3. Run: `python simulate_esp32.py`
4. Open your Render URL in a browser — within ~30-40 seconds it should show LIVE data, cycling through Normal / Partial Discharge / Thermal Fault / Arcing
5. Press Ctrl+C in Command Prompt to stop the simulator whenever you want

## When real ESP32 hardware is ready

Nothing changes on the server. Just:
1. Make sure the ESP32 firmware has the correct WiFi credentials and publishes to the same MQTT broker/topic (`broker.hivemq.com`, topic `transformer/T1/dga`) — same as what's already in your `.ino` firmware
2. Power on the ESP32
3. Stop running `simulate_esp32.py` if it's still running
4. Open the same Render URL — now it shows real sensor data instead of simulated

## Important free-tier note

Render's free tier "sleeps" the service after about 15 minutes of no traffic, and takes ~30-50 seconds to wake up on the next visit. For your review/demo day, simply open the link 1-2 minutes before the panel arrives so it's already awake. This doesn't affect data — the MQTT listener still runs and stores recent history once awake; only the very first visit after a long idle period feels slow.

If you want zero sleep delay even for casual checking, the paid Render tier removes this — not necessary for a college project, just worth knowing as a real fact.

## Troubleshooting

- **Render shows "Application failed to respond"**: check the Render logs tab — usually means a missing file in `models/` or a typo in requirements.txt
- **Dashboard says "NO DATA" forever**: the MQTT listener inside `app.py` couldn't connect, or nothing is publishing yet. Run `simulate_esp32.py` from your laptop to test.
- **"Module not found" during build**: a package name/version issue in `requirements.txt` — paste the exact Render build log error and it can be fixed precisely.
