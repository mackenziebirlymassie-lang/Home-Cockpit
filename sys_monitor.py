"""
Cockpit Hardware Monitor Provider
Extracts real-time CPU, RAM, Disk, and Network telemetry via psutil.
"""
import time
from dataclasses import dataclass
import psutil

def format_speed(bytes_per_sec: float) -> str:
    if bytes_per_sec >= 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
    elif bytes_per_sec >= 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    return f"{bytes_per_sec:.0f} B/s"

@dataclass
class ProcessInfo:
    name: str
    memory_mb: float
    memory_percent: float

@dataclass
class HardwareStats:
    cpu_percent: float
    cpu_count: int
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    net_sent_speed: float
    net_recv_speed: float
    net_sent_speed_str: str
    net_recv_speed_str: str
    top_processes: list[ProcessInfo]
    net_sent_mb: float = 0.0
    net_recv_mb: float = 0.0

class SystemMonitor:
    def __init__(self):
        # Initial call to avoid 0.0 reading on first cpu_percent
        psutil.cpu_percent(interval=None)
        self._last_net = psutil.net_io_counters()
        self._last_net_time = time.time()
        self._cached_procs: list[ProcessInfo] = []
        self._last_proc_check = 0.0

    def get_top_processes(self, limit: int = 3) -> list[ProcessInfo]:
        now = time.time()
        # Cache for 2.5 seconds to prevent excessive CPU consumption during process scans
        if self._cached_procs and (now - self._last_proc_check < 2.5):
            return self._cached_procs

        procs: list[ProcessInfo] = []
        for p in psutil.process_iter(['name', 'memory_info', 'memory_percent']):
            try:
                info = p.info
                name = info.get('name')
                if name and name.lower() not in ('system idle process', 'system'):
                    mem_info = info.get('memory_info')
                    mem_mb = (mem_info.rss / (1024 * 1024)) if mem_info else 0.0
                    mem_pct = info.get('memory_percent') or 0.0
                    procs.append(ProcessInfo(name=name, memory_mb=mem_mb, memory_percent=mem_pct))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by highest RAM usage
        top = sorted(procs, key=lambda x: x.memory_percent, reverse=True)[:limit]
        self._cached_procs = top
        self._last_proc_check = now
        return top

    def get_stats(self) -> HardwareStats:
        cpu = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count(logical=True) or 1
        
        vm = psutil.virtual_memory()
        ram_used = vm.used / (1024 ** 3)
        ram_total = vm.total / (1024 ** 3)
        
        disk = psutil.disk_usage("C:\\")
        disk_used = disk.used / (1024 ** 3)
        disk_total = disk.total / (1024 ** 3)
        
        now = time.time()
        time_delta = max(now - self._last_net_time, 1e-6)
        net = psutil.net_io_counters()
        
        bytes_sent_delta = max(0, net.bytes_sent - self._last_net.bytes_sent)
        bytes_recv_delta = max(0, net.bytes_recv - self._last_net.bytes_recv)
        
        sent_speed = bytes_sent_delta / time_delta
        recv_speed = bytes_recv_delta / time_delta
        
        self._last_net = net
        self._last_net_time = now

        sent_mb = net.bytes_sent / (1024 ** 2)
        recv_mb = net.bytes_recv / (1024 ** 2)
        top_procs = self.get_top_processes(3)

        return HardwareStats(
            cpu_percent=cpu,
            cpu_count=cpu_count,
            ram_percent=vm.percent,
            ram_used_gb=ram_used,
            ram_total_gb=ram_total,
            disk_percent=disk.percent,
            disk_used_gb=disk_used,
            disk_total_gb=disk_total,
            net_sent_speed=sent_speed,
            net_recv_speed=recv_speed,
            net_sent_speed_str=format_speed(sent_speed),
            net_recv_speed_str=format_speed(recv_speed),
            top_processes=top_procs,
            net_sent_mb=sent_mb,
            net_recv_mb=recv_mb,
        )
