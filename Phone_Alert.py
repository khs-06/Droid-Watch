import cv2
import requests
import os
import threading
from time import time, sleep
import numpy as np
from dotenv import load_dotenv
import telegram
import telegram.ext
import sqlite3
from datetime import datetime

# Load environment variables
load_dotenv('config.env')

# Telegram bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_ENABLED = True
if not BOT_TOKEN or BOT_TOKEN.startswith('<'):
    print("⚠️  Warning: BOT_TOKEN not set. Telegram alerts will be disabled.")
    TELEGRAM_ENABLED = False

# ROI and camera configuration
roi_start_point_str = os.getenv('ROI_START_POINT')
roi_end_point_str = os.getenv('ROI_END_POINT')
ip_camera_url = os.getenv("IP_CAMERA_URL")

# ── TUNING SETTINGS (change these to adjust sensitivity) ──────────────────────
MIN_CONTOUR_AREA    = 4000   # lower = detects smaller movements (was 5000)
PERSISTENCE_FRAMES  = 6      # frames motion must persist before alert (was 5)
ALERT_COOLDOWN      = 15     # seconds between alerts (was 10)
WARMUP_FRAMES       = 30     # frames to skip at start so background can learn
BLUR_KERNEL         = (21, 21)  # gaussian blur to reduce noise
MOG2_HISTORY        = 500    # how many frames background model remembers
MOG2_THRESHOLD      = 50     # sensitivity of MOG2 (lower = more sensitive)
# ─────────────────────────────────────────────────────────────────────────────

# Initialize database
def init_db():
    conn = sqlite3.connect('motion_alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            photo_path TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Validate Telegram configuration
if not TELEGRAM_ENABLED:
    CHAT_ID = None
elif not CHAT_ID or CHAT_ID.startswith('<'):
    print("⚠️  Warning: CHAT_ID not set. Telegram alerts will be disabled.")
    CHAT_ID = None

if not ip_camera_url or ip_camera_url.startswith('<'):
    print("⚠️  Warning: IP_CAMERA_URL not set. Using default webcam (0).")
    ip_camera_url = 0

roi_start_point = None
roi_end_point = None

if roi_start_point_str and not roi_start_point_str.startswith('<'):
    try:
        roi_start_point = tuple(map(int, roi_start_point_str.strip().split(',')))
    except ValueError:
        print("⚠️  Invalid ROI_START_POINT. Using full frame.")

if roi_end_point_str and not roi_end_point_str.startswith('<'):
    try:
        roi_end_point = tuple(map(int, roi_end_point_str.strip().split(',')))
    except ValueError:
        print("⚠️  Invalid ROI_END_POINT. Using full frame.")


# ── Send Telegram alert in a background thread so detection doesn't freeze ────
def send_alert(photo_path):
    def _send():
        if not TELEGRAM_ENABLED or CHAT_ID is None:
            print("⚠️  Skipping alert: Telegram not configured")
            return
        if not BOT_TOKEN:
            print("⚠️  Skipping alert: BOT_TOKEN not configured")
            return
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
        try:
            with open(photo_path, 'rb') as photo:
                response = requests.post(
                    url,
                    data={'chat_id': CHAT_ID, 'caption': '🚨 Motion Detected! 📱 Phone Camera Alert'},
                    files={'photo': photo},
                    timeout=10
                )
            if response.status_code == 200:
                print("📸 Alert sent to Telegram!")
                conn = sqlite3.connect('motion_alerts.db')
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO alerts (timestamp, photo_path, message) VALUES (?, ?, ?)',
                    (datetime.now().isoformat(), photo_path, 'Motion detected alert sent')
                )
                conn.commit()
                conn.close()
                print("📊 Alert logged to database")
            else:
                print(f"❌ Telegram error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Send alert exception: {e}")

    # Run in separate thread — detection loop won't pause/freeze
    threading.Thread(target=_send, daemon=True).start()


def send_connection_lost_alert():
    if CHAT_ID is None:
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={'chat_id': CHAT_ID, 'text': '⚠️ Camera connection lost! Check your phone.'},
            timeout=10
        )
        print("⚠️  Connection lost alert sent.")
    except Exception as e:
        print(f"❌ Connection lost alert failed: {e}")


# ── Telegram /check command ───────────────────────────────────────────────────
async def check(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        f"🤖 Bot Status: Active\n"
        f"📱 Camera: {ip_camera_url}\n"
        f"🎯 ROI Start: {roi_start_point}\n"
        f"🎯 ROI End:   {roi_end_point}\n"
        f"📞 Chat ID: {CHAT_ID}\n"
        f"⚙️  Min Area: {MIN_CONTOUR_AREA} | Cooldown: {ALERT_COOLDOWN}s"
    )
    await update.message.reply_text(msg)  # type: ignore


# ── Main motion detection loop ────────────────────────────────────────────────
def motion_detection():
    # Open camera
    if isinstance(ip_camera_url, str):
        cap = cv2.VideoCapture(ip_camera_url)
    else:
        cap = None
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    print(f"📹 Using webcam index {i}")
                    break
                cap.release()
            cap = None
        if cap is None:
            print("❌ Could not open any camera")
            return

    # Set buffer size low so we always get the latest frame (reduces lag)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("🚀 Motion detection started!")
    print(f"   ROI: {roi_start_point} → {roi_end_point}")
    print(f"   Warming up background model ({WARMUP_FRAMES} frames)...")

    # Background subtractor — tuned for phone camera streams
    bg_sub = cv2.createBackgroundSubtractorMOG2(
        history=MOG2_HISTORY,
        varThreshold=MOG2_THRESHOLD,
        detectShadows=False  # shadows off = faster + less false positives
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    frame_count          = 0
    object_frames        = 0
    last_alert_time      = 0
    last_conn_status     = True
    consecutive_failures = 0
    max_failures         = 15

    while True:
        ret, frame = cap.read()

        if not ret:
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                print("❌ Too many failures. Exiting.")
                break
            if last_conn_status:
                send_connection_lost_alert()
                last_conn_status = False
            print("📡 Frame grab failed, retrying...")
            sleep(2)
            continue

        consecutive_failures = 0
        last_conn_status = True
        frame_count += 1

        # ── ROI extraction ─────────────────────────────────────────────────
        if roi_start_point and roi_end_point:
            cv2.rectangle(frame, roi_start_point, roi_end_point, (0, 255, 0), 2)
            roi = frame[roi_start_point[1]:roi_end_point[1],
                        roi_start_point[0]:roi_end_point[0]]
        else:
            roi = frame

        # Skip if ROI is empty (bad coordinates)
        if roi.size == 0:
            print("⚠️  ROI is empty — check your coordinates in config.env")
            continue

        # ── Motion detection pipeline ──────────────────────────────────────
        # Step 1: Blur to reduce noise from phone camera compression
        blurred = cv2.GaussianBlur(roi, BLUR_KERNEL, 0)

        # Step 2: Background subtraction
        fg_mask = bg_sub.apply(blurred)

        # Step 3: Threshold + morphological cleanup
        _, fg_mask = cv2.threshold(fg_mask, 25, 255, cv2.THRESH_BINARY)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)   # remove tiny specks
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)  # fill gaps
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

        # Step 4: Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_found = any(cv2.contourArea(c) > MIN_CONTOUR_AREA for c in contours)

        # Draw contours on frame for visual feedback
        if motion_found and roi_start_point:
            for c in contours:
                if cv2.contourArea(c) > MIN_CONTOUR_AREA:
                    x, y, w, h = cv2.boundingRect(c)
                    # Offset contour to full frame coordinates
                    fx = x + roi_start_point[0]
                    fy = y + roi_start_point[1]
                    cv2.rectangle(frame, (fx, fy), (fx + w, fy + h), (0, 0, 255), 2)

        # ── Warmup: let background model learn before triggering alerts ────
        if frame_count <= WARMUP_FRAMES:
            label = f"Warming up... {frame_count}/{WARMUP_FRAMES}"
            cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            cv2.imshow('Phone Camera Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        # ── Persistence check ──────────────────────────────────────────────
        if motion_found:
            object_frames += 1
        else:
            object_frames = 0

        # ── Status overlay on frame ────────────────────────────────────────
        status = f"MOTION ({object_frames}/{PERSISTENCE_FRAMES})" if motion_found else "Monitoring..."
        color  = (0, 0, 255) if motion_found else (0, 255, 0)
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Cooldown timer display
        elapsed = time() - last_alert_time
        if elapsed < ALERT_COOLDOWN:
            remaining = int(ALERT_COOLDOWN - elapsed)
            cv2.putText(frame, f"Cooldown: {remaining}s", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        # ── Trigger alert ──────────────────────────────────────────────────
        current_time = time()
        if (object_frames >= PERSISTENCE_FRAMES and
                (current_time - last_alert_time) > ALERT_COOLDOWN):
            photo_path = f'motion_alert_{int(current_time)}.jpg'
            cv2.imwrite(photo_path, frame)
            print(f"🚨 Motion alert! Sending snapshot: {photo_path}")
            send_alert(photo_path)
            last_alert_time = current_time
            object_frames = 0

        cv2.imshow('Phone Camera Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("📹 Camera released. Goodbye!")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("📱 Phone Camera Motion Alert System")
    print("=" * 50)
    print(f"📷 Camera  : {ip_camera_url}")
    print(f"🎯 ROI     : {roi_start_point} → {roi_end_point}")
    print(f"📞 Chat ID : {CHAT_ID}")
    print(f"⚙️  Area    : {MIN_CONTOUR_AREA} | Frames: {PERSISTENCE_FRAMES} | Cooldown: {ALERT_COOLDOWN}s")
    print("=" * 50)
    print("Press 'q' in the camera window to quit.")
    print()

    motion_thread = threading.Thread(target=motion_detection, daemon=True)
    motion_thread.start()

    if TELEGRAM_ENABLED and BOT_TOKEN and CHAT_ID:
        app = telegram.ext.ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(telegram.ext.CommandHandler("check", check))
        app.run_polling()
    else:
        print("⚠️  Telegram bot is disabled (BOT_TOKEN/CHAT_ID not configured).")
        print("🔍 Motion detection is still running; close the window or press 'q' to exit.")
        motion_thread.join()