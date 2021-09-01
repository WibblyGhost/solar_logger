# Solar-Logger
Created by: WibblyGhost
 
### Purpose
This project is a multi-step program which relies on a MQTT backend to read information from an Outback solar controller which sends statistics of current battery status, input voltages and etc. This program subscribes to the MQTT broker to retrieve the information broadcasted and deciphers the raw byte streams into a readable form. It then converts the data into points to allow insertion into a time series database (InfluxDB) where the data can be stored, modeled and queried. The database will link to a Grafana website which will graph, model and compare the data on a privately accessible site.
