#!/usr/bin/env python
#===============================================================================
# Copyright (C) 2018 Paul van Veen
#
# This file is part of ginlong-influxdb.
#
# R2_Control is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# R2_Control is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ginlong-influxdb.  If not, see <http://www.gnu.org/licenses/>.
#
# tested with firmware version  H4.01.51Y4.0.0W1.0.57(2017-12-211-D)
#===============================================================================

import paho.mqtt.client as mqtt
import socket
import binascii
import datetime
import sys
import string
import ConfigParser
import io
import json
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError

with open("config.ini") as f:
        sample_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.readfp(io.BytesIO(sample_config))

###########################
# Variables
listen_address = config.get('DEFAULT', 'listen_address') # What address to listen to (0.0.0.0 means it will listen on all addresses)
listen_port = int(config.get('DEFAULT', 'listen_port')) # Port to listen on
client_id = config.get('MQTT', 'client_id') # MQTT Client ID
mqtt_server = config.get('MQTT', 'mqtt_server') # MQTT Address
mqtt_port = int(config.get('MQTT', 'mqtt_port')) # MQTT Port
influx_server = config.get('INFLUXDB', 'influxdb_server') # Ifluxdb server adress
influx_port = int(config.get('INFLUXDB', 'influxdb_port')) # Influxdb port
influx_db = config.get('INFLUXDB', 'influxdb_databasename') # influxdb name
influx_user = config.get('INFLUXDB', 'influxdb_user') # influxdb gebruikersnaam
influx_passwd = config.get('INFLUXDB', 'influxdb_password') # influxdb login


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((listen_address, listen_port))
sock.listen(1)


while True:
    # Wait for a connection
    if __debug__:
        print 'waiting for a connection'
    conn,addr = sock.accept()
    try:
        #print >>sys.stderr, 'connection from', addr
        # while True:
            rawdata = conn.recv(1000) # Read in a chunk of data
            hexdata = binascii.hexlify(rawdata) # Convert to hex for easier processing
	    timestamp = datetime.datetime.now() # get the time
	    if(len(hexdata) == 276):
                serial = binascii.unhexlify(str(hexdata[30:60])) # Serial number is used for MQTT path, allowing multiple inverters to connect to a single instance
                if __debug__:
                    print 'Hex data: %s' % hexdata
                    print "Serial %s" % serial
                    print "Length %s" % len(hexdata)
                mqtt_topic = ''.join([client_id, "/", serial, "/"]) # Create the topic base using the client_id and serial number
                if __debug__:
                    print >>sys.stderr, 'MQTT Topic: ', mqtt_topic

                ##### Calculate Values
                vpv1 = float(int(hexdata[66:70],16))/10
                vpv2 = float(int(hexdata[70:74],16))/10
                ipv1 = float(int(hexdata[78:82],16))/10
                ipv2 = float(int(hexdata[82:86],16))/10
                vac1 = float(int(hexdata[102:106],16))/10
                iac1 = float(int(hexdata[90:94],16))/10
                #pac = float(int(hexdata[118:122],16))
		pac = float((vpv1*ipv1+vpv2*ipv2)*0.975)
                fac = float(int(hexdata[114:118],16))/100
                temp = float(int(hexdata[62:66],16))/10
                kwhtoday = float(int(hexdata[138:142],16))/100
                kwhtotal = float(int(hexdata[146:150],16))/10

		# adjust first value of the day
		dayinit = open("initday.txt","r+")
		day = timestamp.strftime("%d")
		if float(dayinit.readline()) != day:
			if pac == 0 : kwhtoday = float(0)
			else: dayinit.write(day)
		dayinit.close()

		#### Build Json string
		DataJson = [ {"measurement":"SolarPanel",
				"tags":{"Unit": serial},
				"fields": {
					"VoltagePv1":vpv1,
					"VoltagePv2":vpv2,
					"CurrentPv1":ipv1,
					"CurrentPv2":ipv2,
					"LineVoltage":vac1,
					"LineCurrent":iac1,
					"SolarPower":pac,
					"Frequency":fac,
					"Temperatuur":temp,
					"kwhtoday":kwhtoday,
					"kwhtotal":kwhtotal
					  }
			     }
			  ]

		if __debug__:
		    print "Json Buffer %s" % DataJson
		    file = open("rawlog",'a')
                    file.write(timestamp.strftime('%d %b %Y - %H:%M:%S') + ' ' + hexdata + '\n')
                    file.close()


		#### Publish data
		if influx_db:
			client = InfluxDBClient(influx_server,influx_port, influx_user , influx_passwd , influx_db)
			client.create_database (influx_db)
                	client.write_points (DataJson,protocol='json')

		if mqtt_server:
			client = mqtt.Client(client_id)
			client.connect(mqtt_server)
			client.publish(mqtt_topic, payload=json.dumps(DataJson))

    finally:
        if __debug__:
            print "Finally"
