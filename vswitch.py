########################################################################################################################
#
#
#  	Project     	: 	Valveswitch
#
#   File            :   vswitch.py
#
#	By              :   George Leonard ( georgelza@gmail.com )
#
#   Created     	:   8 Apr 2023
#
#   Notes       	:   monitor a set of mqtt topics and toggle gpio pins accordingly.
#
#                   :   mqtt: http://www.steves-internet-guide.com/subscribing-topics-mqtt-client/
#                   :   gpio: https://gist.github.com/johnwargo/ea5edc8516b24e0658784ae116628277
#
#
#                   :   sudo cp gardenvalve.service /etc/systemd/system/gardenvalve.service
#                   :   sudo systemctl daemon-reload
#                   :   sudo systemctl enable garden.service
#                   :   sudo systemctl start garden.service
#                   :   sudo systemctl status garden.service
#
#
#
#######################################################################################################################

__author__      = "George Leonard"
__email__       = "georgelza@gmail.com"
__version__     = "0.0.1"
__copyright__   = "Copyright 2022, George Leonard"


#import RPi.GPIO as GPIO
import statistics
import time, sys, os, json
from datetime import datetime
from pprint import pprint
#from influxdb import InfluxDBClient
from apputils import *
import paho.mqtt.client as mqtt
import logging
# https://gpiozero.readthedocs.io/en/stable/installing.html
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

configfile      = os.getenv('CONFIGFILE')
config_params   = get_config_params(configfile)

DEBUGLEVEL      = int(config_params['common']['debuglevel'])
LOGLEVEL        = config_params['common']['loglevel'].upper()
LOGFILE         = config_params['common']['logfile'].lower()
SWITCHES        = config_params['common']['switches']

l_switches      = []
l_subjects      = []
l_pinList       = []

# Set up root logger, and add a file handler to root logger
#my_logger.basicConfig(filename='garden.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

FORMAT = '%(levelname)s :%(message)s'
logging.basicConfig(filename=LOGFILE, 
    filemode='w', 
    encoding='utf-8',
    level = logging.INFO,
    format= FORMAT)

# create logger
my_logger = logging.getLogger(__name__)
# create console handler and set level to debug
my_logger_shandler = logging.StreamHandler()
my_logger.addHandler(my_logger_shandler)

print_params(configfile, my_logger)


if LOGLEVEL == 'INFO':
    my_logger.setLevel(logging.INFO)
    my_logger.info('INFO LEVEL Activated')

elif LOGLEVEL == 'DEBUG':
    my_logger.setLevel(logging.DEBUG)
    my_logger.info('DEBUG LEVEL Activated')

elif LOGLEVEL == 'CRITICAL':
    my_logger.setLevel(logging.CRITICAL)
    my_logger.info('CRITICAL LEVEL Activated')


########################################################################################################################
#
#   Ok Lets start things
#
########################################################################################################################


############# Instantiate a connection to the MQTT Server ##################
def mqtt_connect():

    # Configure the Mqtt connection etc.
    broker      = config_params["mqtt"]["broker"]
    port        = int(config_params["mqtt"]["port"])
    clienttag   = config_params["mqtt"]["clienttag"]
    username    = config_params["mqtt"]["username"]
    password    = config_params["mqtt"]["password"]

    my_logger.info("#####################################################################")
    my_logger.info("")

    my_logger.debug('{time}, Creating connection to MQTT... '.format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        ))

    my_logger.debug('{time}, Broker                  : {broker} '.format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        broker=broker
        ))

    my_logger.debug('{time}, Port                    : {port}'.format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        port=port
        ))

    my_logger.debug('{time}, Client Tag              : {clienttag} '.format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        clienttag=clienttag
        ))

        
    mqtt.Client.connected_flag      = False                     # this creates the flag in the class
    mqtt.Client.bad_connection_flag = False                     # this creates the flag in the class

    client = mqtt.Client(clienttag)                             # create client object client1.on_publish = on_publish #assign function to callback
                                                                # client1.connect(broker,port) #establish connection client1.publish("house/bulb1","on")

    ##### Bind callback functions
    client.on_connect       = on_connect  # bind my on_connect to client
    client.on_log           = on_log  # bind my on_log to client
    client.on_message       = on_message  # bind my on_message to client
    client.on_disconnect    = on_disconnect
    client.on_publish       = on_publish
    client.on_subscribe     = on_subscribe

    try:
        client.username_pw_set(username, password)
        client.connect(broker, port)                                          # connect

        my_logger.info("{time}, Connected to MQTT broker: {broker}, Port: {port}".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            broker=broker,
            port=port
        ))

        my_logger.info("")
        my_logger.info("#####################################################################")
        my_logger.info("")

    except Exception as err:
        my_logger.error("{time}, Connection to MQTT Failed... {broker}, Port: {port}, Err: {err}".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            broker=broker,
            port=port,
            err=err
        ))

        my_logger.error("")
        my_logger.error("#####################################################################")
        my_logger.error("")

        sys.exit(1)

    return client
#end mqtt_connect


#define callbacks
def on_connect(client, userdata, flags, rc):

    if rc == 0:
        client.connected_flag = True
        my_logger.debug("{time}, MQTT, connected OK".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        ))

    else:
        my_logger.error("{time}, MQTT, Bad connection, {rc}".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            rc=rc
        ))
        client.bad_connection_flag = True

#end on_connect


def on_log(client, userdata, level, buf):

    my_logger.debug("{time}, MQTT, log {buf}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        buf=buf
    ))

#end on_log


def relay_on(pin):
    GPIO.output(pin, GPIO.LOW)
    my_logger.debug("{time}, Switched to {gpiostate}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        gpiostate=GPIO.LOW,
        ))
    
def relay_off(pin):
    GPIO.output(pin, GPIO.HIGH)
    my_logger.debug("{time}, Switched to {gpiostate}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        gpiostate=GPIO.HIGH,
        ))

def s_toggle(gpio, state):

    if state == "ON":
        relay_on(gpio)
        my_logger.debug("{time}, Switch Toggled: gpio: {gpio} ON".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            gpio=gpio,
        ))
    elif state == "OFF":
        relay_off(gpio)
        my_logger.debug("{time}, Switch Toggled: gpio: {gpio} OFF".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            gpio=gpio,
        ))
    else:
        print("go ERROR")
        my_logger.debug("{time}, Switch NOT ad valid target state".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        ))

#end s_toggle


def on_message(client, userdata, message):

    topic = message.topic
    m_decode = str(message.payload.decode("utf-8"))

    my_logger.info("{time}, MQTT, received message : {topic}, {payload}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        topic=topic,
        payload=json.dumps(m_decode, indent=2, sort_keys=True),
    ))

    # Figure out which switch we're working on based on the topic
    switch = l_subjects.index(topic)

    # find the gpio pin for the switch
    gpio = l_switches[l_subjects.index(topic)]["gpio"]

    my_logger.debug("{time}, Switch Toggled: {topic}, payload: {payload}, switch: {switch}, gpio: {gpio}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        topic=topic,
        payload=json.dumps(m_decode, indent=2, sort_keys=True),
        switch=switch,
        gpio=gpio,
    ))

    # Toggle the switch based on gpio pin to desired state
    s_toggle(gpio, m_decode)

#end on_message


def on_publish(client, userdata, mid):

    my_logger.debug("{time}, MQTT, Subscribed :{mid}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        mid=mid
    ))

#end on_publish


def on_subscribe(client, userdata, mid, granted_qos):

    my_logger.debug("{time}, MQTT, Subscribed :".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
    ))

#end on_subscribe


def on_disconnect(client, userdata, flags, rc=0):

    if DEBUGLEVEL > 2: 
        my_logger.info("{time}, MQTT, Disconnected {rc} :".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            rc=rc
        ))
    client.connected_flag = False

#end on_disconnect


def publishMQTT(client, json_data, topic):

    try:
        ret = client.publish(topic, json_data, 0)           # QoS = 0
        my_logger.debug("{time}, MQTT, Publish returned: {ret}".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            ret=ret
        ))

    except Exception as err:
        my_logger.error('{time}, MQTT, Publish Failed !!!: {err}'.format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            err=err
        ))

#end publishMQTT


def switch_configs(client):

    switches = config_params["common"]["switches"].split(",")

    my_logger.debug("{time}, MQTT, Configured Switches {switches}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        switches=switches
    ))

    for switch in switches:
        json_switch = {
                "name":             config_params[switch]["name"],
                "base_topic":       config_params[switch]["base_topic"],
                "power_topic":      config_params[switch]["power_topic"],
                "qos":              int(config_params[switch]["qos"]),
                "gpio":             int(config_params[switch]["gpio"]),
                "default_state":    config_params[switch]["default_state"],
        }
        l_switches.append(
            json_switch
        )
        publishMQTT(client, json.dumps(json_switch), config_params[switch]["base_topic"])

    my_logger.debug("{time}, Switch Configs {json_switches}".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        json_switches=json.dumps(l_switches, indent=3)
    ))

    return l_switches
#end switch_configs


def compile_topics(switches):

    topics = []
    for switch in switches:
        my_logger.debug("{time}, Input switch config {switch}".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            switch=switch
        ))
        topics.append(
                [switch["power_topic"], switch["qos"]]
        )
        l_subjects.append(switch["power_topic"])
        l_pinList.append([ switch["gpio"], switch["default_state"] ])

    return topics
#end compile_topics


def Initialize_switches():

    my_logger.debug("{time}, GPIO Initialize Start".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
    ))

    # loop through pins and set mode and state to 'low'
    for i in l_pinList:
        pin             = i[0]
        default_state   = i[1]

        GPIO.setup(pin, GPIO.OUT)

        my_logger.debug("{time}, GPIO {pin} Initialized as: Output".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            pin=pin,
        ))

        if default_state == "HIGH":
            GPIO.output(pin, GPIO.HIGH)

        elif default_state == "LOW":
            GPIO.output(pin, GPIO.LOW)

        my_logger.debug("{time}, GPIO {pin} Initialized to: {default_state}".format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            pin=pin,
            default_state=default_state,
        ))

    my_logger.debug("{time}, GPIO Initialize Complete".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
    ))

#end Initialize_switches


def switching():

    my_logger.info("{time}, Entering main(): ".format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
    ))

    try: 

        # Create the MQTT connection
        client = mqtt_connect()

        # Retrieve topics to subscribe to
        s_configs   = switch_configs(client)
        s_topics    = compile_topics(s_configs)

        Initialize_switches()

        # Subscribe to topics
        client.subscribe(s_topics)

        # Start listening on topics
        client.loop_start()
        run_flag = True
        while run_flag == True:

            if DEBUGLEVEL > 3:
                my_logger.debug("{time}, in main wait loop".format(
                    time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
                ))

            time.sleep(int(config_params["common"]["sleep"]))

    except Exception as err:

        my_logger.error('{time}, Something went wrong... Err: {err}'.format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
            err=err
        ))
  
    except KeyboardInterrupt:

        # Reset by pressing CTRL + C
        my_logger.error('{time}, Shutting Down (CTRL + C)...'.format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
        ))

        sys.stdout.flush()
        sys.exit(-1)

    finally:

        # Cleanup, Disconnect
        my_logger.info('{time}, MQTT, Disconnecting... '.format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        ))
        client.disconnect()  # disconnect

        my_logger.info('{time}, GPIO, Cleanup... '.format(
            time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
        ))
        GPIO.cleanup()

    my_logger.info('{time}, Goodbye... '.format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
    ))

#end go_switching


if __name__ == '__main__':

    my_logger.info("")
    my_logger.info('{time}, Starting... '.format(
        time=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")),
    ))

    switching()
# end def


