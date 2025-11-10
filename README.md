# 🐋 Whale Tracking Bot

A simple Telegram bot that captures a snapshot of the *Assets* section from [HyperDash.info](https://hyperdash.info) trader pages.

## 🚀 Features
- Takes a full-page screenshot via `thum.io` API.
- Crops the bottom section (Assets area).
- Sends image back to the Telegram chat.
- Works with both `0x` addresses and direct URLs.

## 🧰 Requirements
- Python 3.10+
- Telegram Bot Token

## 📦 Installation
```bash
pip install -r requirements.txt
