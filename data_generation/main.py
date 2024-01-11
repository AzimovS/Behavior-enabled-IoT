import paho.mqtt.client as mqtt
from random import randint
import time
import configparser
import threading

config = configparser.ConfigParser()
config.read('config.ini')

# Load MQTT configuration from file
client_address = config['mqtt']['client_address']
port = int(config['mqtt']['port'])

boats_num = int(config['data_generation']['boats'])
trawlers_num = int(config['data_generation']['trawlers'])
animals_num = int(config['data_generation']['animals'])
time_sleep = int(config['data_generation']['time_sleep'])


def generate_initial_locations(num):
    return [[randint(0, 100), randint(0, 100)] for _ in range(num)]


# Function to publish area data to MQTT broker
def publish_location_data(mqtt_client, locations, source):
    while True:
        topic = f"{source}/location"
        # Generate locations data
        for i in range(len(locations)):
            locations[i][0] += randint(-1, 1)
            locations[i][1] += randint(-1, 1)
            mqtt_client.publish(topic, f'{{"x":{locations[i][0]}, "y":{locations[i][1]}}}')
            print(f"Published {topic} {i}: x:{locations[i][0]}, y:{locations[i][1]}")
        
        time.sleep(time_sleep)  # Breaks between publishing data (defined in config)


if __name__ == "__main__":
    mqtt_client = mqtt.Client()
    mqtt_client.connect(client_address, port=port)

    boats_locations = generate_initial_locations(boats_num)
    trawlers_locations = generate_initial_locations(trawlers_num)
    animals_locations = generate_initial_locations(animals_num)

    threads=[]
    thread1 = threading.Thread(target=publish_location_data, args=(mqtt_client, animals_locations, 'animal'))
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
