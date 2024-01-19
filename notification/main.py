import math
import os
from time import sleep
from dotenv import load_dotenv
from telegram import Bot, ParseMode
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')


BUCKET = "locations"
org = "archiwizards"
token = "sa_token"
url = "172.30.0.102:8086"
threshold_distance = 100  # threshold distance in kilometers

client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

query_api = client.query_api()


def calculate_distance(coord1, coord2):
    # Haversine formula to calculate distance between two coordinates on Earth
    R = 6371  # Earth radius in kilometers

    lat1, lon1 = coord1[3], coord1[4]
    lat2, lon2 = coord2[3], coord2[4]

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c  # Distance in kilometers
    return round(distance, 2)


def send_telegram_alert(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message,
                        parse_mode=ParseMode.MARKDOWN)


def check_proximity(group1, group2, threshold):
    for item1 in group1:
        for item2 in group2:
            distance = calculate_distance(item1, item2)
            if distance < threshold:
                alert_message = f"ALERT: {item1[2].split('/')[0]} with id {item1[0]} is close to {item2[2].split('/')[0]} with id {item2[0]}. Distance: {distance} km"
                send_telegram_alert(alert_message)


def get_data(group):
    res = []
    query = f'from(bucket: "{BUCKET}")\
    |> range(start: -6h)\
    |> filter(fn: (r) => r["_field"] == "latitude" or r["_field"] == "longitude")\
    |> filter(fn: (r) => r["topic"] == "{group}/location")\
    |> last()\
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")\
    |> group()'

    query_res = query_api.query(org=org, query=query)

    for table in query_res:
        for record in table.records:
            date_time = record.get_time().strftime("%d/%m/%Y-%H:%M:%S")
            res.append([record['id'], date_time, record['topic'],
                       record['latitude'], record['longitude']])
    return res


if __name__ == "__main__":
    while True:
        group_animals = get_data('animals')
        group_boats = get_data('boats')
        group_trawlers = get_data('trawlers')

        # group_animals = [['0', '13/01/2024-17:08:09', 'animals/location', 18.838164439057895, -42.64734224376835], ['1', '13/01/2024-17:08:09', 'animals/location', 32.37881194194833, -27.196973134564047], ['2', '13/01/2024-17:08:09', 'animals/location', -52.915742241622084, 40.09191755459409], ['3', '13/01/2024-17:08:09', 'animals/location', 54.06448006880345, 34.67737608256414]]
        # group_boats = [['0', '13/01/2024-17:08:09', 'boats/location', 18.638164439057895, -42.64734224376835], ['1', '13/01/2024-17:08:09', 'boats/location', 82.8841434507357, -39.42589029253409]]
        # group_trawlers = [['0', '13/01/2024-17:08:09', 'trawlers/location', 6.424314459629073, -31.37127515217544], ['1', '13/01/2024-17:08:09', 'trawlers/location', 86.2360675897414, -39.56656221537918], ['2', '13/01/2024-17:08:09', 'trawlers/location', 1.4911104951686003, -39.03488784178664]]

        check_proximity(group_animals, group_boats, threshold_distance)
        check_proximity(group_animals, group_trawlers, threshold_distance)
        sleep(5)
