import socket
import time
import traceback

import psutil

from modules import logger

io, last_captured_time = psutil.net_io_counters(pernic=True), time.time()

def collect_data():
    try:
        global io, last_captured_time
        io_2, recent_captured_time = psutil.net_io_counters(pernic=True), time.time()
        delay = recent_captured_time - last_captured_time
        data = {}
        for iface, iface_io in io.items():
            upload_speed, download_speed = io_2[iface].bytes_sent - iface_io.bytes_sent, io_2[iface].bytes_recv - iface_io.bytes_recv
            data.update({
                f"{iface}_download": io_2[iface].bytes_recv,
                f"{iface}_upload": io_2[iface].bytes_sent,
                f"{iface}_upload_speed": round(upload_speed / delay) ,
                f"{iface}_download_speed": round(download_speed / delay),
            })
        io, last_captured_time = io_2, recent_captured_time
        data.update({"host": socket.gethostname()})
        return data
    except Exception:
        logger.debug(f"Failed to capture network stats {traceback.format_exc()}")
        return {}