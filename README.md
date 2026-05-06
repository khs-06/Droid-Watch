# DroidWatch — Motion Detection System

Real-time mobile surveillance system using smartphone camera with instant Telegram alerts.

## Tech Stack
- Python 3.x
- OpenCV
- Telegram Bot API
- MySQL

## Features
- ROI-based motion detection
- Real-time snapshot alerts via Telegram bot
- Low-latency frame processing
- Android camera integration via IP camera

## How to Run
1. Clone the repo
git clone https://github.com/khs-06/Droid-Watch.git
2. Install dependencies
pip install opencv-python python-telegram-bot requests
3. Configure your Telegram Bot token in the config file
4. Run the project
pip install opencv-python python-telegram-bot requests
3. Configure your Telegram Bot token in the config file
4. Run the project
python main.py

## Project Highlights
- Designed and implemented motion detection using OpenCV
- Integrated Telegram Bot API for real-time alerts and notifications
- Developed ROI-based detection to improve accuracy and reduce false alerts
- Implemented efficient real-time processing without database dependency