"""
Home Cockpit - Terminal HUD & System Deck
Powered by Textual & Rich
"""
import os
import datetime
from textual.app import App, ComposeResult
from textual.containers import Grid, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Digits, Sparkline, TextArea
from textual.reactive import reactive
from sys_monitor import SystemMonitor
from media_tracker import get_current_media_track

class ClockWidget(Static):
    """Live updating military/digital clock with date banner."""
    def on_mount(self) -> None:
        self.update_time()
        self.set_interval(1.0, self.update_time)

    def update_time(self) -> None:
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %b %d, %Y")
        self.update(f"[bold cyan]{time_str}[/]\n[dim]{date_str}[/]")

class MetricBar(Static):
    """Visual progress bar for percentage metrics."""
    def render_bar(self, label: str, value: float, unit: str = "%", color: str = "green") -> str:
        bar_len = 16
        filled = int((value / 100.0) * bar_len)
        filled = max(0, min(bar_len, filled))
        bar = f"[{color}]{'█' * filled}[/][dim white]{'░' * (bar_len - filled)}[/]"
        return f"[bold]{label:<6}[/] {bar} [bold {color}]{value:5.1f}{unit}[/]"

class HardwareWidget(Static):
    """Live hardware monitors for CPU, RAM, Disk, and Network."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitor = SystemMonitor()
        self.cpu_history: list[float] = [0.0] * 30

    def compose(self) -> ComposeResult:
        yield Static("[bold yellow]⚡ SYSTEM TELEMETRY[/bold yellow]", id="hw-title")
        yield Static(id="cpu-display")
        yield Sparkline(self.cpu_history, summary_function=max, id="cpu-sparkline")
        yield Static(id="ram-display")
        yield Static(id="disk-display")
        yield Static(id="net-display")
        yield Static(id="procs-display")

    def on_mount(self) -> None:
        self.update_stats()
        self.set_interval(1.0, self.update_stats)

    def update_stats(self) -> None:
        stats = self.monitor.get_stats()
        
        # Color coding thresholds
        cpu_col = "green" if stats.cpu_percent < 60 else ("yellow" if stats.cpu_percent < 85 else "red")
        ram_col = "green" if stats.ram_percent < 70 else ("yellow" if stats.ram_percent < 85 else "red")
        disk_col = "green" if stats.disk_percent < 75 else ("yellow" if stats.disk_percent < 90 else "red")

        bar_util = MetricBar()
        cpu_text = bar_util.render_bar("CPU", stats.cpu_percent, "%", cpu_col)
        ram_text = bar_util.render_bar("RAM", stats.ram_percent, "%", ram_col) + f" [dim]({stats.ram_used_gb:.1f}/{stats.ram_total_gb:.1f} GB)[/]"
        disk_text = bar_util.render_bar("C:\\", stats.disk_percent, "%", disk_col) + f" [dim]({stats.disk_used_gb:.0f}/{stats.disk_total_gb:.0f} GB)[/]"
        net_text = f"[bold cyan]NET SPEED[/] [dim]▲ {stats.net_sent_speed_str:<8}  ▼ {stats.net_recv_speed_str}[/]"

        top_text = "\n[bold yellow]🔥 TOP CONSUMERS (RAM)[/]"
        if stats.top_processes:
            for i, p in enumerate(stats.top_processes, 1):
                name = p.name if len(p.name) <= 15 else p.name[:12] + "..."
                top_text += f"\n[dim]{i}.[/] [white]{name:<15}[/] [dim]({p.memory_mb:.0f} MB - {p.memory_percent:.1f}%)[/]"
        else:
            top_text += "\n[dim]Scanning processes...[/]"

        self.query_one("#cpu-display", Static).update(cpu_text)
        self.query_one("#ram-display", Static).update(ram_text)
        self.query_one("#disk-display", Static).update(disk_text)
        self.query_one("#net-display", Static).update(net_text)
        self.query_one("#procs-display", Static).update(top_text)

        # Update sparkline
        self.cpu_history.pop(0)
        self.cpu_history.append(stats.cpu_percent)
        self.query_one("#cpu-sparkline", Sparkline).data = list(self.cpu_history)

class NowPlayingWidget(Static):
    """Live Windows Media Session Now Playing deck."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]🎵 NOW PLAYING[/bold magenta]", id="media-title")
        yield Static(id="media-content")

    def on_mount(self) -> None:
        self.set_interval(1.5, self.update_media)

    async def update_media(self) -> None:
        track = await get_current_media_track()
        if track.status == "Playing":
            icon = "▶"
            status_style = "bold green"
        elif track.status == "Paused":
            icon = "⏸"
            status_style = "bold yellow"
        else:
            icon = "⏹"
            status_style = "dim"

        album_text = f"\n[dim]{track.album}[/]" if track.album else ""
        content = (
            f"[{status_style}]{icon} {track.status.upper()}[/]\n\n"
            f"[bold white]{track.title}[/]\n"
            f"[cyan]{track.artist}[/]{album_text}"
        )
        try:
            self.query_one("#media-content", Static).update(content)
        except Exception:
            pass

NOTES_FILE = "scratchpad.txt"
DEFAULT_NOTES = """# 🎯 MISSION OBJECTIVES
- [ ] Monitor system telemetry & network
- [ ] Track active media stream
- [ ] Review sprint backlog

# 💡 QUICK SCRATCHPAD
Type notes or tasks here... Auto-saves live!
"""

class ScratchpadWidget(Static):
    """Interactive persistent scratchpad."""
    def compose(self) -> ComposeResult:
        yield Static("[bold green]📝 SCRATCHPAD & MISSION NOTES[/bold green] [dim](auto-saved)[/dim]", id="notes-title")
        initial_text = DEFAULT_NOTES
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        initial_text = content
            except Exception:
                pass
        else:
            try:
                with open(NOTES_FILE, "w", encoding="utf-8") as f:
                    f.write(initial_text)
            except Exception:
                pass

        yield TextArea(initial_text, id="scratchpad-area")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        try:
            with open(NOTES_FILE, "w", encoding="utf-8") as f:
                f.write(event.text_area.text)
        except Exception:
            pass

class CockpitApp(App):
    """The Home Cockpit Terminal TUI application."""
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1 2;
        padding: 1;
        background: $background;
    }

    #clock-box {
        border: heavy cyan;
        height: 100%;
        content-align: center middle;
        text-align: center;
        background: $surface;
    }

    #hw-box {
        border: heavy yellow;
        height: 100%;
        padding: 1 2;
        background: $surface;
    }

    #cpu-sparkline {
        height: 2;
        margin-bottom: 1;
        color: yellow;
    }

    #procs-display {
        margin-top: 1;
    }

    #media-box {
        border: heavy magenta;
        height: 100%;
        padding: 1 2;
        background: $surface;
    }

    #notes-box {
        border: heavy green;
        height: 100%;
        padding: 1 1;
        background: $surface;
    }

    #scratchpad-area {
        height: 1fr;
        margin-top: 1;
        border: none;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Vertical(ClockWidget(), id="clock-box")
        yield Vertical(HardwareWidget(), id="hw-box")
        yield Vertical(NowPlayingWidget(), id="media-box")
        yield Vertical(ScratchpadWidget(), id="notes-box")
        yield Footer()

if __name__ == "__main__":
    app = CockpitApp()
    app.run()
