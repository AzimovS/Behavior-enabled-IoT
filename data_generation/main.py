import paho.mqtt.client as mqtt
from random import randint, random
from json import dumps
import time
import configparser
import threading

config = configparser.ConfigParser()
config.read('config.ini')

# Load MQTT configuration from file
client_address = config['mqtt']['client_address']
port = int(config['mqtt']['port'])

animals_num = int(config['data_generation']['animals'])
boats_num = int(config['data_generation']['boats'])
trawlers_num = int(config['data_generation']['trawlers'])
time_sleep = int(config['data_generation']['time_sleep'])


def generate_initial_locations(num):
    # latitude and longitude
    return [[randint(-45, 45), randint(-90, 90), random()] for _ in range(num)]


# Function to publish area data to MQTT broker
def publish_location_data(mqtt_client, locations, source):
    while True:
        topic = f"{source}/location"
        # Generate locations data
        for i in range(len(locations)):
            locations[i][0] += randint(-1, 1) * locations[i][2]
            locations[i][1] += randint(-1, 1) * locations[i][2]
            payload = {"longitude":locations[i][0], "latitude":locations[i][1], "id":i}
            payload_json = dumps(payload)
            mqtt_client.publish(topic, payload_json)
            
            print(f"Published {topic} {i}: longitude:{locations[i][0]}, latitude:{locations[i][1]}")
        
        time.sleep(time_sleep)  # Breaks between publishing data (defined in config)


if __name__ == "__main__":
    mqtt_client = mqtt.Client()
    mqtt_client.connect(client_address, port=port)

    animals_locations = generate_initial_locations(animals_num)
    boats_locations = generate_initial_locations(boats_num)
    trawlers_locations = generate_initial_locations(trawlers_num)

    threads=[]
    thread1 = threading.Thread(target=publish_location_data, args=(mqtt_client, animals_locations, 'animals'))
    thread2 = threading.Thread(target=publish_location_data, args=(mqtt_client, boats_locations, 'boats'))
    thread3 = threading.Thread(target=publish_location_data, args=(mqtt_client, trawlers_locations, 'trawlers'))
    threads.append(thread1)
    threads.append(thread2)
    threads.append(thread3)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete (which they won't, as they're infinite loops)
    for thread in threads:
        thread.join()
