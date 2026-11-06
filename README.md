# 🛸 Home Cockpit

A high-density personal telemetry and productivity HUD built in Python using **Textual** and **Rich**.

Designed to run full-screen in Windows Terminal on your primary or secondary display.

## 🚀 Features
- **⚡ System Telemetry**: Real-time CPU, RAM, Disk, and live network throughput (upload/download speed in KB/s / MB/s) with color-graded status thresholds, live CPU sparkline graphs, and top memory-consuming processes.
- **🎵 Now Playing Deck**: Live integration with Windows Media Control (Spotify, YouTube, browser audio) showing current track title, artist, album, and playback status.
- **🕒 Precision Military Clock**: Instant time and calendar orientation.
- **📝 Interactive Scratchpad**: Real-time in-app multi-line text editor with automatic live disk persistence (`scratchpad.txt`) for objectives and focus tracking.
- **🕹️ Keyboard Driven**: 
  - `Q` / `Ctrl+Q`: Quit Cockpit
  - `D`: Toggle high-contrast / dark themes

## 🛠️ Quick Start

### 1. Launch directly:
Double-click `run.bat` or run:
```powershell
cd C:\Users\Kenny\Documents\Projects\home-cockpit
.\venv\Scripts\python.exe cockpit.py
```
