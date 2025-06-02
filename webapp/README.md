# Air Quality Monitor Webapp

This web application visualizes real-time air quality data from the BME68X sensor. It provides a responsive user interface with gauges, graphs, and export functionality.

## Features

- Real-time display of air quality, temperature, and humidity
- Responsive design for mobile and desktop
- Light/Dark mode
- Offline functionality (PWA)
- CSV data export
- Automatic updates
- Interactive data visualization

## Prerequisites

- Python 3.8 or higher
- pip (Python Package Manager)
- InfluxDB 2.x
- A BME68X sensor with running data collection script

## Installation

1. Clone the repository or navigate to the webapp directory:
```bash
cd webapp
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the InfluxDB connection:
   - Copy `app.ini.example` to `app.ini` (if it doesn't exist)
   - Edit `app.ini` and add your InfluxDB credentials:
```ini
[InfluxDB]
url = http://localhost:8086
token = YOUR_INFLUXDB_TOKEN
org = YOUR_ORG_NAME
bucket = YOUR_BUCKET_NAME
```

## Deployment

### Development Server

For testing purposes, you can use the built-in Flask development server:

```bash
python app.py
```

The webapp will be accessible at `http://localhost:5000`.

### Production Deployment

For production use, it's recommended to use a WSGI server:

1. Install Gunicorn (Linux/Mac only):
```bash
pip install gunicorn
```

2. Start the application with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Für Windows-Server wird die Verwendung von Waitress empfohlen:

1. Installieren Sie Waitress:
```bash
pip install waitress
```

2. Starten Sie die Anwendung:
```bash
waitress-serve --port=5000 app:app
```

### Nginx als Reverse Proxy (empfohlen)

1. Installieren Sie Nginx:
```bash
sudo apt install nginx  # Debian/Ubuntu
```

2. Erstellen Sie eine Nginx-Konfiguration:
```nginx
server {
    listen 80;
    server_name ihr-server-name.de;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /pfad/zu/ihrer/webapp/static;
        expires 30d;
    }
}
```

3. Aktivieren Sie die Konfiguration:
```bash
sudo ln -s /etc/nginx/sites-available/ihre-config /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Systemd Service (für automatischen Start)

1. Erstellen Sie eine Service-Datei:
```bash
sudo nano /etc/systemd/system/air-quality-webapp.service
```

2. Fügen Sie folgende Konfiguration ein:
```ini
[Unit]
Description=Air Quality Monitor Webapp
After=network.target

[Service]
User=ihr-user
WorkingDirectory=/pfad/zu/ihrer/webapp
Environment="PATH=/pfad/zu/ihrer/webapp/venv/bin"
ExecStart=/pfad/zu/ihrer/webapp/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

3. Aktivieren und starten Sie den Service:
```bash
sudo systemctl enable air-quality-webapp
sudo systemctl start air-quality-webapp
```

## SSL/TLS Encryption

For HTTPS encryption, it's recommended to use Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-server-name.com
```

## Monitoring

The application can be monitored using various tools. Recommended setup:

1. Prometheus for metrics
2. Grafana for visualization
3. Loki for log aggregation

## Maintenance

- Perform regular InfluxDB data backups
- Set up log rotation
- Keep dependencies updated
- Monitor system resources

## Troubleshooting

Check the logs:
```bash
sudo journalctl -u air-quality-webapp
```

Common issues:
- InfluxDB connection errors
- Permission issues
- Port conflicts
- Memory usage

## Lizenz

Siehe LICENSE-Datei im Hauptverzeichnis.
