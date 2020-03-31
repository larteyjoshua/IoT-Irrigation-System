"""
This module is the generator which select data from DB 
and prepares the data into csv format for download

Date: 31st May, 2019
Author: John PK Erbynn - john.erbynn@gmail.com
"""

import csv
import psycopg2
def generate_csv_file(parameter):
    # database connection
    con = psycopg2.connect("dbname='IotIrrigation' user='postgres' host='localhost' password='12345678'")
    cursor = con.cursor()

    # selecting particular water parameter data from DB
    cursor.execute(" SELECT id, time, %s FROM SensorRecords ORDER BY id" %parameter) 
    data = cursor.fetchall()
    data = list(data)
    
    # generating a list within a list
    toList = []
    for d in data:
        l = list(d)
        toList.append(l)

    # creating csv file and writing the data(2 leveled list) into it 
    with open(f'data/IoTIrrigationSystem_{parameter}_data.csv', 'w') as csvFile:
        writer = csv.writer(csvFile, delimiter=',')
        writer.writerow(['id', 'timestamp', parameter])
        writer.writerows(toList)
        csvFile.close()


# generate_csv_file(some_parameter)