# DroidWatch — Motion Detection Using Phone Camera and Bot Integration

A real-time mobile surveillance system that uses a smartphone camera to detect motion 
within a defined Region of Interest (ROI). On detection, the system captures a snapshot 
and sends instant alerts via Telegram bot.

## Tech Stack
- Python 3.x
- OpenCV (MOG2 background subtraction)
- Telegram Bot API (python-telegram-bot)
- SQLite (motion alert logging)
- python-dotenv (config management)

## Features
- ROI-based motion detection to reduce false alerts
- Real-time snapshot alerts via Telegram bot
- Automatic camera connection lost alert
- SQLite database logging with timestamp and photo path
- CSV export of alert history
- /check bot command to verify system config remotely
- Configurable via config.env — no code changes needed

## How to Run
1. Clone the repo
   git clone https://github.com/khs-06/Droid-Watch.git

2. Install dependencies
   pip install opencv-python python-telegram-bot requests python-dotenv

3. Configure config.env
   BOT_TOKEN = your_telegram_bot_token
   CHAT_ID = your_chat_id
   ROI_START_POINT = 100,100
   ROI_END_POINT = 400,300
   IP_CAMERA_URL = http://your_phone_ip:8080/video

4. Select ROI coordinates
   python ROI_point_finder.py

5. Run the system
   python Phone_Alert.py

## Project Highlights
- Implemented MOG2 background subtraction with Gaussian blur for accurate detection
- Built ROI coordinate selector tool for easy zone configuration
- Motion persists for 6 consecutive frames before alert triggers — eliminates noise
- Alert cooldown of 15 seconds prevents spam notifications
- All alerts logged to SQLite with photo path and timestamp
- Developed and tested during internship at Chronex Technologies (Dec 2025 - Mar 2026)