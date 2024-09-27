# System Monitoring Scripts

Modified for Monitoring End to End KVM + Libvirt Machines

## Prerequisites

Make sure you have the following installed on your system:

- Python 3.x
- InfluxDB
- [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)

## Usage

1. Set up your InfluxDB configuration by creating a `.env` file with the following variables:

    ```env
    INFLUX_URL="https://your-influxdb-url:8086"
    INFLUX_TOKEN="your-influxdb-token"
    INFLUX_ORG="your-influxdb-organization"
    INFLUX_BUCKET="your-influxdb-bucket"
    ```
2. Run the script:

    ```bash
    python system_monitor.py
    ```

