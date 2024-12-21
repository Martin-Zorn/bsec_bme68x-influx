# bsec_bme68x-influx

Fork of [bsec_bme680-homie](https://github.com/alaub81/bsec_bme680-homie).
Tested with a Raspberry Pi 4 and BSEC version 2.6.1.0.

Here you can find a complete small application, which uses the [Bosch Sensortec Environmental Cluster](https://www.bosch-sensortec.com/software-tools/software/bme680-software-bsec/) (BSEC) to read out the data from the BME68x Sensor and writes it to an InfluxDB.

# Requirements
* BME68x Sensor
* Raspberry Pi (4)
* [BSEC Library](https://www.bosch-sensortec.com/software-tools/software/bme680-software-bsec/)

# Building besc_bme68x
Please download the [BSEC Library](https://www.bosch-sensortec.com/software-tools/software/bsec/) to `./src`.
Configure build with the make.config.
Use the make.sh to patch and build the binary.

# Using the bsec_bme68x-influx.py
Please add your credentials to bsec_bme68x-influx.ini.

<!---
# Configuration

## Systemd Service
---!>

