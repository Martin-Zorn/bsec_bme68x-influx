#!/usr/bin/env python3

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import configparser
import json
import subprocess
import os


if __name__ == "__main__":
    bin_dir = os.path.join(os.path.dirname(__file__), "../bin")
    bsec_bme68x_path = os.path.join(bin_dir, "bsec_bme68x")
    config_path = os.path.join(os.path.dirname(__file__), "bsec_bme68x-influx.ini")

    os.chdir(bin_dir)

    config = configparser.ConfigParser()
    config.read(config_path)

    write_client = InfluxDBClient(
        url=config["InfluxDB"]["url"],
        token=config["InfluxDB"]["token"],
        org=config["InfluxDB"]["org"],
    )
    write_api = write_client.write_api(write_options=SYNCHRONOUS)

    try:
        proc = subprocess.Popen([bsec_bme68x_path], stdout=subprocess.PIPE)

        lineDict = {}

        for line in iter(proc.stdout.readline, ""):
            try:
                lineJSON = json.loads(line.decode("utf-8"))
                lineDict = dict(lineJSON)
            except Exception as e:
                print(f"Can't parse {line}, error: {e}")
                continue

            point = (
                Point("air_quality")
                .tag("device", "bme68x")
                .field("Temperature", float(lineDict["Temperature"]))
                .field("Humidity", float(lineDict["Humidity"]))
                .field("Gas", float(lineDict["Gas"]))
                .field("Pressure", float(lineDict["Pressure"]))
                .field("IAQ_Accuracy", int(lineDict["IAQ_Accuracy"]))
                .field("IAQ", float(lineDict["IAQ"]))
                .field("Static_IAQ", float(lineDict["Static_IAQ"]))
                .field("eCO2", float(lineDict["eCO2"]))
                .field("bVOCe", float(lineDict["bVOCe"]))
                .field("Status", int(lineDict["Status"]))
            )

            try:
                write_api.write(
                    bucket=config["InfluxDB"]["bucket"],
                    org=config["InfluxDB"]["org"],
                    record=point,
                )
            except Exception as e:
                print(f"Can't write to InfluxDB, error: {e}")

    except Exception as e:
        print(f"Can't start bsec_bme68x, error: {e}")
