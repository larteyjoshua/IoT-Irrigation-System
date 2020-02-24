import sqlite3
import random
import datetime
import time

con = sqlite3.connect('IotIrrigation.db')
# con = sqlite3.connect(':memory:') # when db locks
cursor = con.cursor()

def create_table():

        cursor.execute( 
                """ CREATE TABLE IF NOT EXISTS SensorRecords( 
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        Time TIMESdTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        temperature REAL, 
                        water_used REAL, 
                        ph REAL, 
                        moisture REAL) """)
                        
        print('...inside create db fxn') 

# if not included, creates only DB without any table    
create_table()