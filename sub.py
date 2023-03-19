import re
from typing import NamedTuple
import paho.mqtt.client as mqtt
#from influxdb import InfluxDBClient
import mariadb
import json
import csv
import pandas as pd




# CONSTANTS
DB_ADDRESS = 'localhost'
DB_USER = 'aba275'
DB_PASSWORD = 'password'
DB_NAME = 'seeed-weather'


MQTT_ADDRESS = 'weather2.iot.nau.edu'
MQTT_USER = 'akiel'
MQTT_PASSWORD = 'password'
MQTT_TOPIC = 'nau-iot/+/+'
MQTT_REGEX = 'nau-iot/([^/]+)/([^/]+)'

#influxdb_client = InfluxDBClient(DB_ADDRESS,
#                                 8086,
#                                 DB_USER,
#                                 DB_PASSWORD,
#                                 None)





def on_connect(client, userdata, flags, rc):
    print("[+] CONNECTION WITH CODE : " + str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    mqtt_topic = msg.topic
    mqtt_topic_msg = str(msg.payload.decode('utf-8'))
    
    msg_data = json.loads(mqtt_topic_msg)
    json_msg = pd.json_normalize(json.loads(msg_data))

    #json_msg.Date = pd.to_datetime(json_msg['time'])
    #json_msg.set_index('time')
    #json_msg.index = pd.to_datetime(json_msg.index, unit='ns').astype(int)
    print(json_msg)

    if json_msg is not None:
        DB_insert(json_msg)

def DB_insert(df):
    """
    Inserts a pandas DataFrame into a MariaDB table.

    Parameters:
    df (pandas.DataFrame): the DataFrame to insert into the table.

    Returns:
    None
    """
    try:
        conn = mariadb.connect(user='aba275',
                               password='',
                               host='localhost',
                               port=3306,
                               database='SEEED_WEATHER')
        cursor = conn.cursor()

        # create the table if it doesn't exist
        create_table_query = """CREATE TABLE IF NOT EXISTS mqtt_data (
                                id INT NOT NULL AUTO_INCREMENT,
                                time BIGINT NOT NULL,
                                temperature FLOAT,
                                humidity FLOAT,
                                pressure FLOAT,
                                light_intensity FLOAT,
                                min_wind_direction FLOAT,
                                max_wind_direction FLOAT,
                                avg_wind_direction FLOAT,
                                min_wind_speed FLOAT,
                                max_wind_speed FLOAT,
                                avg_wind_speed FLOAT,
                                accum_rainfall FLOAT,
                                accum_rainfall_duration FLOAT,
                                rainfall_intensity FLOAT,
                                max_rainfall_intensity FLOAT,
                                heating_temperature FLOAT,
                                dumping_of_state FLOAT,
                                pm2_5 FLOAT,
                                pm10 FLOAT,
                                PRIMARY KEY (id)
                                );"""

        cursor.execute(create_table_query)

        # insert data into the table
        for index, row in df.iterrows():
            insert_query = f"""INSERT INTO mqtt_data (
                               time,
                               temperature,
                               humidity,
                               pressure,
                               light_intensity,
                               min_wind_direction,
                               max_wind_direction,
                               avg_wind_direction,
                               min_wind_speed,
                               max_wind_speed,
                               avg_wind_speed,
                               accum_rainfall,
                               accum_rainfall_duration,
                               rainfall_intensity,
                               max_rainfall_intensity,
                               heating_temperature,
                               dumping_of_state,
                               pm2_5,
                               pm10
                               )
                               VALUES (
                               {row['time']},
                               {row['Temperature']},
                               {row['Humidity']},
                               {row['Pressure']},
                               {row['Light Intensity']},
                               {row['Min Wind Direction']},
                               {row['Max Wind Direction']},
                               {row['AVG Wind Direction']},
                               {row['Min Wind Speed']},
                               {row['Max Wind Speed']},
                               {row['AVG Wind Speed']},
                               {row['Accum Rainfall']},
                               {row['Accum Rainfall Duration']},
                               {row['Rainfall Intensity']},
                               {row['Max Rainfall Intensity']},
                               {row['Heating Temperature']},
                               {row['The dumping of state']},
                               {row['PM2.5']},
                               {row['PM10']}
                               )"""

            cursor.execute(insert_query)

        # commit changes and close connection
        conn.commit()
        cursor.close()
        conn.close()

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")


def parse_mqtt_msg(topic, payload):
    """
    reads variables from topic path struct and identifies vars
    returning them as the a named tuple
    """
    # create match var = to first match of two vars passed in
    match = re.match(MQTT_REGEX, topic)
    # return named tuple if match
    if match:
        location = match.group(1)
        measurement = match.group(2)
        if measurement == 'status':
            return None
        return SensorData(location, measurement, float(payload))
    else:
        return None


def main():
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_ADDRESS, 1883, 60)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.loop_forever()


if __name__ == '__main__':
    print('** MQTT -> MariaDB bridge **')
    main()

