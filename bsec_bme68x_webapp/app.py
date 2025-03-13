from flask import Flask, jsonify, render_template, request, send_from_directory, Response
from influxdb_client import InfluxDBClient
import configparser
import os
import json
import time

app = Flask(__name__, static_folder='static')

# InfluxDB connection details
INFLUXDB_URL = ["InfluxDB"]["url"]
INFLUXDB_TOKEN = ["InfluxDB"]["url"]
INFLUXDB_ORG = ["InfluxDB"]["org"]
INFLUXDB_BUCKET = ["InfluxDB"]["bucket"]

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)
query_api = client.query_api()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    duration = request.args.get('duration', '-1h')
    interval = request.args.get('interval', '1m')

    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: {duration})
      |> filter(fn: (r) => r._measurement == "air_quality" and r.device == "bme68x")
      |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
      |> yield(name: "mean")
    '''
    
    result = query_api.query(org=INFLUXDB_ORG, query=query)
    
    data = {metric: [] for metric in [
        "Temperature", "Humidity", "Gas", "Pressure", 
        "IAQ", "Static_IAQ", "eCO2", "bVOCe", "Status"
    ]}
    
    latest_data = {}

    for table in result:
        for record in table.records:
            metric = record.get_field()
            time = record.get_time().isoformat()
            value = record.get_value()
            
            if metric in data:
                data[metric].append({"time": time, "value": value})
                
                if metric not in latest_data or time > latest_data.get(metric, {}).get("time", ""):
                    latest_data[metric] = {"time": time, "value": value}

    data['latest'] = {metric: latest_data[metric]['value'] for metric in latest_data if latest_data[metric]['value'] is not None}

    return jsonify(data)

@app.route('/api/stream')
def stream():
    def event_stream():
        while True:
            query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -10s)
              |> filter(fn: (r) => r._measurement == "air_quality" and r.device == "bme68x")
              |> last()
            '''
            result = query_api.query(org=INFLUXDB_ORG, query=query)
            
            latest_data = {}
            for table in result:
                for record in table.records:
                    metric = record.get_field()
                    value = record.get_value()
                    if metric in ["IAQ", "Temperature", "Humidity"]:
                        latest_data[metric] = value
            
            if latest_data:
                # Log the data to see what's being sent
                print("Sending data via SSE:", latest_data)
                yield f"data: {json.dumps(latest_data)}\n\n"
            else:
                print("No new data found.")

            time.sleep(4)
    
    return Response(event_stream(), content_type='text/event-stream')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run()
