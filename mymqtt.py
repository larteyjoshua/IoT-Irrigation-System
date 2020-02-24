#!/usr/bin/env python
import cayenne.client
import logging

# Cayenne authentication info. This should be obtained from the Cayenne Dashboard.
MQTT_USERNAME  = "ad26ad00-51cd-11ea-84bb-8f71124cfdfb"
MQTT_PASSWORD  = "587b2e983174306428bd5312229324c8681f74ec"
MQTT_CLIENT_ID = "0afe9940-532e-11ea-84bb-8f71124cfdfb"


# The callback for when a message is received from Cayenne.
def on_message(message):
    print("message received: " + str(message))
    # If there is an error processing the message return an error string, otherwise return nothing.

client = cayenne.client.CayenneMQTTClient()
client.on_message = on_message
client.begin(MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID)
# For a secure connection use port 8883 when calling client.begin:
# client.begin(MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID, port=8883, loglevel=logging.INFO)
client.loop_forever()