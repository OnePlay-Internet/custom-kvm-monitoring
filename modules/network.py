# import psutil
# from time import sleep
#
# def get_network_data(interface):
#     stats_before = psutil.net_io_counters(pernic=True)[interface]
#     sleep(5)  # Adjust the sleep duration as needed
#     stats_after = psutil.net_io_counters(pernic=True)[interface]
#
#     receive_bytes = stats_after.bytes_recv - stats_before.bytes_recv
#     transmit_bytes = stats_after.bytes_sent - stats_before.bytes_sent
#
#     return receive_bytes, transmit_bytes
#
# def main():
#     network_interface = "enp6s0"
#     interval_seconds = 5
#
#     try:
#         while True:
#             receive_bytes, transmit_bytes = get_network_data(network_interface)
#
#             print(f"Network Interface: {network_interface}")
#             print(f"Received Data: {receive_bytes} bytes")
#             print(f"Transmitted Data: {transmit_bytes} bytes")
#             print("=" * 30)
#
#             sleep(interval_seconds)
#
#     except KeyboardInterrupt:
#         print("Script terminated by user.")
import socket
import subprocess


def get_network_io() -> dict:
    try:
        # Read the contents of /proc/net/dev
        result = subprocess.run(['cat', '/proc/net/dev'], capture_output=True, text=True, check=True)

        # Split the output into lines
        lines = result.stdout.splitlines()

        # Initialize a dictionary to hold network I/O stats
        network_io = {}

        # Process each line
        for line in lines[2:]:  # Skip the first two header lines
            parts = line.split(':')
            if len(parts) > 1:
                interface = parts[0].strip()
                stats = parts[1].strip().split()
                # Assuming stats[0] is bytes received and stats[8] is bytes transmitted
                bytes_received = int(stats[0])
                bytes_transmitted = int(stats[8])
                network_io.update({
                    f'{interface}_received': bytes_received,
                    f'{interface}_transmitted': bytes_transmitted
                })

        return network_io

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return {}


def collect_data():
    try:
        net_stats = get_network_io()
        net_stats.update({"host": socket.gethostname()})
        return net_stats
    except Exception as e:
        print(str(e))
    return {}
