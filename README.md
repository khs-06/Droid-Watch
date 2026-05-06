#  � Phone Camera Motion Detection with Telegram Alerts
[![License](https://img.shields.io/github/license/whitehatboy005/Motion-Detection-Alert-System-for-CCTV)](LICENSE.md)

This repository contains two main tools:
1. **ROI Selector Tool**: A graphical tool to help users easily select a Region of Interest (ROI) from the screen.
2. **Phone Camera Motion Detection Tool**: A mobile surveillance system that monitors your phone's camera feed for motion within the defined ROI and sends alerts via Telegram.

##  🚀 Features
### 1. ROI Point Finder Tool:
- Graphically select the **Region of Interest (ROI)** on your screen.
- Print the start and end coordinates of the ROI for use in motion detection.
- Simplifies the process of defining an ROI for motion detection.

### 2. Phone Camera Motion Detection Tool:
- **Monitor your phone's camera**: Use IP Webcam apps to stream your phone's camera and detect motion in a specified area.
- **Send Telegram alerts**: When motion is detected, a snapshot of the frame is sent to a Telegram chat.
- **Configurable settings**: Set up the Telegram Bot Token, Phone Camera URL, and ROI coordinates via environment variables.
- **Efficient motion detection**: Only monitors motion within the defined ROI to minimize unnecessary alerts.
- **Database logging**: All alerts are logged to a local SQLite database for historical tracking and analysis.
#
## 📌 Instructions
To get Chat ID visit [@GetMyChatID_Bot](https://t.me/GetMyChatID_Bot) Now you will copy the chat Id and config it.

To access the bot [@SecurityAlertBot](http://t.me/CAMSEC_AlertBot) and START it.
#
## Start the Telegram Bot
![Screenshot 2024-12-13 104535](https://github.com/user-attachments/assets/22b7d49f-11ed-41c1-ab90-90339fe06ab1)
## Program Running interface
![Screenshot 2024-12-13 104848](https://github.com/user-attachments/assets/e546e0a9-aea9-4187-b11e-f51f96c52d9e)
## Telegram Bot Alert
![Screenshot 2024-12-13 111934](https://github.com/user-attachments/assets/9b307fa0-4e57-4bc3-bc48-a4e02e8916b4)
#
## ⚙️ Installation
## Clone the Repository
```bash
git clone https://github.com/whitehatboy005/Motion-Detection-Alert-System-for-CCTV
cd Motion-Detection-Alert-System-for-CCTV
```
## Install Dependencies
```bash
pip install -r requirements.txt
```
## Find ROI Point for alert zone
```bash
python ROI_point_finder.py
```
## Configure Environment Variables
Create or edit `config.env` and set your values (replace placeholders):

```text
BOT_TOKEN=123456:ABCdefGhIJKlmNoPQRsTuvWxYZ
CHAT_ID=123456789
ROI_START_POINT=100,100
ROI_END_POINT=400,300
IP_CAMERA_URL=http://192.168.x.x:8080/video
```

Edit the file with:

```bash
notepad config.env
```

## Ensure start the bot
## Database
The project uses SQLite (built-in with Python) to log all motion alerts. The database file `motion_alerts.db` will be created automatically. You can query it using any SQLite browser or Python scripts for analysis.
Start it --> [@SecurityAlertBot](http://t.me/CAMSEC_AlertBot)
#
## Run the main Program
```bash
python Phone_Alert.py
```
#
## To check on configuration in Telegram
Type [/check] Then check it out.
#
## WEBCAM Motion Detection Alert System Repository for project submission
  **Check on this repository** https://github.com/whitehatboy005/Motion-Detection-Alert-System-for-Webcam
#

## 👨‍💻 Contribution:
**Contributions are welcome! If you have any suggestions for improvements or bug fixes, feel free to submit a pull request.**

## 📝 License
This project is licensed under the terms of the [MIT license](LICENSE.md).
