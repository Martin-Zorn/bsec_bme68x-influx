from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_from_directory,
    Response,
)
from influxdb_client import InfluxDBClient
import configparser
import os
import json
import csv
import io
from datetime import datetime

app = Flask(__name__, static_folder="static")

config_path = os.path.join(os.path.dirname(__file__), "app.ini")
config = configparser.ConfigParser()
config.read(config_path)

# InfluxDB connection details
INFLUXDB_URL = config["InfluxDB"]["url"]
INFLUXDB_TOKEN = config["InfluxDB"]["token"]
INFLUXDB_ORG = config["InfluxDB"]["org"]
INFLUXDB_BUCKET = config["InfluxDB"]["bucket"]

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)
query_api = client.query_api()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def get_data():
    try:
        duration = request.args.get("duration", "-1h")
        interval = request.args.get("interval", "1m")
        
        app.logger.info(f"Fetching data with duration: {duration}, interval: {interval}")

        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: {duration})
            |> filter(fn: (r) => r._measurement == "air_quality" and r.device == "bme68x")
            |> filter(fn: (r) => r._field == "Temperature" or r._field == "Humidity" or 
                            r._field == "Gas" or r._field == "Pressure" or 
                            r._field == "IAQ" or r._field == "Static_IAQ" or 
                            r._field == "eCO2" or r._field == "bVOCe" or 
                            r._field == "Status")
            |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
            |> yield(name: "mean")
        '''
        
        app.logger.info(f"Running query: {query}")
        result = query_api.query(org=INFLUXDB_ORG, query=query)
        app.logger.info("Query executed successfully")

        data = {
            "Temperature": [], "Humidity": [], "Gas": [], "Pressure": [],
            "IAQ": [], "Static_IAQ": [], "eCO2": [], "bVOCe": [], "Status": []
        }
        
        record_count = 0
        for table in result:
            for record in table.records:
                record_count += 1
                field = record.get_field()
                timestamp = record.get_time().isoformat()
                value = record.get_value()
                
                app.logger.debug(f"Record: field={field}, time={timestamp}, value={value}")
                
                if field in data:
                    data[field].append({"time": timestamp, "value": value})

        app.logger.info(f"Processed {record_count} records")
        
        # Get latest values
        latest = {}
        for field in data:
            if data[field]:  # If we have any data for this field
                latest[field] = data[field][-1]["value"]  # Get the last value
        
        data["latest"] = latest
        
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f"Error in get_data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/latest")
def get_latest_data():
    """
    Polling API to return the latest air quality metrics.
    """
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -30s)
      |> filter(fn: (r) => r._measurement == "air_quality" and r.device == "bme68x")
      |> filter(fn: (r) => r._field == "Temperature" or r._field == "Humidity" or r._field == "IAQ")
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

    return jsonify(latest_data)


@app.route("/api/export")
def export_data():
    """
    Export data as CSV file
    """
    duration = request.args.get("duration", "-1h")
    interval = request.args.get("interval", "1m")

    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: {duration})
      |> filter(fn: (r) => r._measurement == "air_quality" and r.device == "bme68x")
      |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
      |> yield(name: "mean")
    '''

    result = query_api.query(org=INFLUXDB_ORG, query=query)

    # Create StringIO object for CSV writing
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Write header
    cw.writerow(['Timestamp', 'Metric', 'Value'])
    
    # Write data
    for table in result:
        for record in table.records:
            cw.writerow([
                record.get_time().isoformat(),
                record.get_field(),
                record.get_value()
            ])

    output = si.getvalue()
    si.close()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=air_quality_data_{duration}.csv"}
    )


@app.route("/api/debug")
def debug_data():
    """
    Debug endpoint to check raw data from InfluxDB
    """
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "air_quality")
    '''

    result = query_api.query(org=INFLUXDB_ORG, query=query)
    debug_data = []

    for table in result:
        for record in table.records:
            debug_data.append({
                'time': record.get_time().isoformat(),
                'measurement': record.get_measurement(),
                'field': record.get_field(),
                'value': record.get_value(),
                'tags': record.values
            })

    return jsonify({
        'data_points': len(debug_data),
        'sample_data': debug_data[:5] if debug_data else [],
        'fields_found': list(set(d['field'] for d in debug_data)),
        'config': {
            'bucket': INFLUXDB_BUCKET,
            'org': INFLUXDB_ORG,
            'url': INFLUXDB_URL
        }
    })


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    app.debug = True  # Enable debug mode
    app.run()
