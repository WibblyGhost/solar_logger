# Solar-Logger
Created by: WibblyGhost & Jorticus
 
### Purpose
This project was made to subscribe to a solar MQTT provider which reports several battery and input details received from an Outback controller system. This particular MQTT provider and libraries required to decode the raw byte streams were provided by Jorticus. After deciphering the raw packets this program will unload the categories into a time series database for Jorticus to relay to his web portal. 
