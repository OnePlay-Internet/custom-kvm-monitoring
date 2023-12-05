import os
import time
import subprocess
import re
import socket
from dotenv import load_dotenv
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()

def get_system_uptime_seconds():
	try:
		uptime_output = subprocess.check_output(['uptime']).decode('utf-8').strip()
		uptime_match = re.search(r"up(?:\s+)?((\d+) days?,)?(?:\s+)?(\d+):(\d+)", uptime_output)

		if uptime_match:
			days, _, hours, minutes = map(lambda x: int(x) if x else 0, uptime_match.groups())

			uptime_seconds = days * 24 * 60 * 60 + hours * 60 * 60 + minutes * 60

			return uptime_seconds
		else:
			raise ValueError("Unable to parse uptime information")

	except Exception as e:
		print(f"Error: {e}")
		return None



def collect_and_send_metrics(interval_seconds):
	influx_url = os.getenv("INFLUX_URL")
	influx_token = os.getenv("INFLUX_TOKEN")
	influx_org = os.getenv("INFLUX_ORG")
	influx_bucket = os.getenv("INFLUX_BUCKET")

	client = influxdb_client.InfluxDBClient(
			 url=influx_url,
			 token=influx_token,
			 org=influx_org
	)

	write_api = client.write_api(write_options=SYNCHRONOUS)
	hostname = socket.gethostname()

	while True:
		uptime_seconds = get_system_uptime_seconds()
		point = influxdb_client.Point("uptime") \
							   .tag("host", hostname) \
							   .field("uptime", uptime_seconds)

		write_api.write(bucket=influx_bucket, org=influx_org, record=point)
		time.sleep(interval_seconds)


def test(interval_seconds):
	while True:
		time.sleep(interval_seconds)
		print(f"{time.time()} - uptime module")

	
if __name__=="__main__":
	collect_and_send_metrics()
