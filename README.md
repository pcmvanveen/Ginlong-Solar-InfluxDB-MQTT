# Overview
 
This is a daemon that will listen on a port for connections from a Ginlong Solar Inverter. Currently tested with a Solis 4G single Phase Inverter (Solis-mini-1500-4G firmware version H4.01.51Y4.0.02W1.0.57 (2017-12-211-D)

Many thanks go to Graham0 and his script for an older version. https://github.com/graham0/ginlong-wifi

# Details
The Solis solar inverters come with the option for wired or wireless monitoring 'sticks'. These are designed to talk to their own portal at http://www.ginlongmonitoring.com/ where
the stats will gather. This software allows you to run your own gatherer on a server and push these stats into an MQTT queue for use in other systems such as the OpenHAB home
automation software. It is also possable to fill your own influxDB database. There is no need to send all data to ginlong anymore. 

You will need a system running python with the following modules:
* paho.mqtt.publish
* socket
* binascii
* time
* sys
* string
* influxdb
* json

You will also need a running MQTT server.
To store values in the database you need a running influxDB server(version 1.4 or higher is recomended)


# Setup

1. Log into the monitoring device, and configure the second IP option to point to the server that this daemon is running on. (Daemon defaults to port 9999)
2. Make sure that the MQTT and INFLUXDB settings are correct in the daemon (config.ini file). If yoy do not want to use the MQTT option or the Influx option, you only have to remove the values behind the keyś. Do not remove the keyś self.  
3. Start the daemon
4. Add the following to your OpenHAB items (Replace XXXXXXXXXX with the serial number of your inverter)
```
// Environmentals
Number Solis_Temp "Temperature [%.2f °C]" (Solis) { mqtt="<[mymosquitto:ginlong/XXXXXXXXXX/Temp:state:default" }

// DC
Number Solis_DC1Volt "DC Volts [%.2f V]" (Solis) { mqtt="<[mymosquitto:ginlong/XXXXXXXXXX/Vpv1:state:default" }
Number Solis_DC1Amp "DC Current [%.2f A]" (Solis) { mqtt="<[mymosquitto:ginlong/XXXXXXXXXX/Ipv1:state:default" }

// AC
Number Solis_AC1Volt "AC Volts [%.2f V]" (Solis) { mqtt="<[mymosquitto:ginlong/XXXXXXXXXX/Vac1:state:default" }
Number Solis_AC1Amp "AC Current [%.2f A]" (Solis) { mqtt="<[mymosquitto:ginlong/XXXXXXXXXX/Iac1:state:default" }

// Stats
Number Solis_kWhToday "kWh today [%.2f kWh]" (Solis) { mqtt="<[mymosquitto:ginlong/XXXXXXXXXX/kwhtoday:state:default" }
Number Solis_kWhTotal "kWh total [%.2f kWh]" (Solis) { mqtt="<[mymosquitto:ginlong/XXXXXXXXXX/kwhtotal:state:default" }
```
5. These items should now be accessible in your rules. If you have influxdb and grafana set up, you should also be able to start producing graphs




