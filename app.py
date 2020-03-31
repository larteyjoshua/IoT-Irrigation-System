from flask import Flask, render_template, flash, redirect, request, jsonify, url_for, Response
# from aquaLite import *
import datetime
import json
import time
import statistics as stat
import mail
from config import credential
import generator
from flask_toastr import Toastr     # toastr module import
import paho.mqtt.client as mqtt
import json
import psycopg2


app = Flask(__name__)

# python notification toaster
toastr = Toastr(app)

# Set the secret_key on the application to something unique and secret.
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'


# home route....landing page
@app.route("/", methods = ['GET', 'POST'])
@app.route("/index", methods=["GET", "POST"])
def index():
    print("landing page running...")
    if request.method == 'POST':
        username = request.form['username']
        passwd = request.form['password']

        # credentials from config files imported
        if username == credential['name'] and passwd == credential['passwd']:
            flash('Login successful :)', 'success')
            # flash("You have successfully logged in.", 'success')    # python Toastr uses flash to flash pages
            return redirect(url_for('dashboard')) 
        else:
            flash('Login Unsuccessful. Please check username and password', 'error')

    return render_template("index.html", todayDate=datetime.date.today(), )


def on_connect(client, userdata, rc):
    if rc == 0:
          print("Connected successfully.")
    else:
         print("Connection failed. rc= "+str(rc))

def on_publish(client, userdata, mid):
    print("Message "+str(mid)+" published.")
    
def on_subscribe(client, userdata, mid, granted_qos):
     print("Subscribe with mid "+str(mid)+" received.")

def on_message(client, userdata, msg):
    print("Topic: ", msg.topic)
    print("Messages: ", str(msg.payload.decode("utf-8")))
    if (msg.topic)==("/larteyjoshua@gmail.com/test"):
        print(" Pump is ",str(msg.payload.decode("utf-8")))
    if (msg.topic)==("/larteyjoshua@gmail.com/SensorData"):
        print("Sensor Reading update")
        data= json.loads(msg.payload.decode("utf-8"))

       
        print("connecting to DB")
        # con = sqlite3.connect(':memory:') # when db locks
        con = psycopg2.connect("dbname='IotIrrigation' user='postgres' host='localhost' password='12345678'")
        cursor = con.cursor()
        print("connect to DB")   
        
        #  print("creating  DB")
        #  cursor.execute("CREATE TABLE SensorRecords(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, time TIMESdTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,temperature REAL,water_used REAL,ph REAL,moisture REAL);")
        # # cursor.commit()
                                
        # # print('...inside create db fxn') 

        # # # if not included, creates only DB without any table    
        cursor = con.cursor()

        print('before try...')
        try:
            cursor.execute(""" INSERT INTO SensorRecords( temperature, water_used, ph, moisture) 
                            VALUES (%s, %s, %s, %s) """,
                    (data["temperature"], data["waterused"], data["ph"], data["moisture"]))
            con.commit()
            cursor.close()
            con.close()
            print("Data posted SUCCESSFULLY")
        except Exception as err:
            print('...posting data FAILED')
            print(err)
            
    
   
mqttclient = mqtt.Client()

                # Assign event callbacks
mqttclient.on_connect = on_connect
mqttclient.on_publish = on_publish
mqttclient.on_subscribe = on_subscribe
mqttclient.on_message = on_message

                # Connect
mqttclient.username_pw_set("larteyjoshua@gmail.com", "7f8a9110")
mqttclient.connect("mqtt.dioty.co", 1883)

                # Start subscription
mqttclient.subscribe("/larteyjoshua@gmail.com/test")
mqttclient.subscribe("/larteyjoshua@gmail.com/SensorData")

mqttclient.subscribe("/larteyjoshua@gmail.com/SystemInfo")

           # Publish a message
mqttclient.publish("/larteyjoshua@gmail.com/SystemInfo", "Front End Connected to the Broker")

mqttclient.loop_start()





# empty list to be used for all parameter route
time = []
ph=[]
temp= []
moisture= []
water_used=[]

# initial temps
average_temp = 0
min_temp=0
max_temp=0
range_temp = 0






@app.route("/tempChart/<x>")
def temperature(x):
    print(">>> temperature page running ...")
    # connecting to datebase
    con = psycopg2.connect("dbname='IotIrrigation' user='postgres' host='localhost' password='12345678'")
    cursor = con.cursor()

    #  30secs time interval for pushing data from sensor to database, that the limit of data to be determined  
    
    # data processing for an hour 
    if x == '1h':
        name = '1 Hour'
        label = 'Minute'

        # with 30 seconds interval, ...2,880 temperature data will be posted within an hour
        cursor.execute("SELECT time,temperature FROM ( SELECT * from SensorRecords ORDER BY id DESC LIMIT 120 )as x order by id asc ") 
        data = cursor.fetchall()
        
        # emptying list 
        del time[:]
        del temp[:]
    
        for datum in data:
            # print(datum)
            # temperature data extraction
            datum_float = float(datum[1])
            temp.append(datum_float)
            # time extraction
            t = str(datum[0])[14:]
            time.append(t)
        
        # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


        # data processing for a day
    
    if x == '1d':
        name = '1 Day'
        label = 'Hour'
    
        cursor.execute(" SELECT time,temperature FROM SensorRecords ORDER BY id ASC LIMIT 2880 ") 
        data = cursor.fetchall()

        del time[:] # time on the x-axis
        del temp[:]
    
        for datum in data:
            # print(datum)
            datum_float = float(datum[1])
            temp.append(datum_float)
            t = str(datum[0])[11:16]
            time.append(t)
        
        # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # weekly data processing ,,,,,

    if x == '1w':
        name = '1 Week'
        label = 'Day'

        # fetching data from database
        cursor.execute(" SELECT time,temperature FROM SensorRecords ORDER BY id ASC LIMIT 20160") 
        data = cursor.fetchall()
        
        # converting timestamp from database to day in string like Mon, Tue
        def date_to_day(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%a"))

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving weekly time and temp from database data
        for datum in data:
            # collecting temperature
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list

            # string day processing from full timestamp
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # using full_date to day_string function defined 
            current_day = date_to_day(year, month, day)
            time.append(current_day)
            
        # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # monthly data processing

    if x == '1m':
        name = '1 Month'
        label = 'Month-Date'

        # fetching data from database.....change number of data to fetch
        cursor.execute(" SELECT time,temperature FROM SensorRecords ORDER BY id ASC LIMIT 87600") 
        data = cursor.fetchall()
        
        # retreiving month string from timestamp of database to get sth like January, Febuary
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving monthly time and temp from database data
        for datum in data:
            # collecting temperature
            # print(datum)
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list

            # string month processing from full date timestamp
            tm = str(datum[0])[5:10]
            time.append(tm)

         # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # yearly data processing

    if x == '1y':
        name = '1 Year'
        label = 'Month'

        # fetching data from database.....change number of data to fetch
        cursor.execute(" SELECT time,temperature FROM SensorRecords ORDER BY id ASC LIMIT 1051333") 
        data = cursor.fetchall()
        
         # retreiving month string from timestamp of database to get sth like January, Febuary
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving monthly time and temp from database data
        for datum in data:
            # collecting temperature
            # print(datum)
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list

            # string month processing from full date timestamp
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # using full_date to day_string function defined 
            current_month = string_month_from_full_date(year, month, day)
            time.append(current_month)
            # time.append(year)
            
         # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp


    # all data processing

    if x == 'all':
        name = 'All'
        label = 'Time'

        # fetching data from database.....change number of data to fetch
        # cursor.execute(" SELECT time,temperature FROM iot_wqms_table ORDER BY id DESC LIMIT 1440") 
        cursor.execute(" SELECT time,temperature FROM ( SELECT * from SensorRecords ORDER BY id DESC ) as x order by id asc") 
        data = cursor.fetchall()

        # emptying time and temperature container list
        del time[:]
        del temp[:]

        # retrieving monthly time and temp from database data
        for datum in data:
            # collecting temperature
            # print(datum)
            datum_float = float(datum[1])   # temp data in float
            temp.append(datum_float)        # pushing to temp list
            # string month processing from full date timestamp
            tm = str(datum[0])[:7]
            time.append(tm)
            
         # analysis
        mean_temp = stat.mean(temp)
        average_temp = round(mean_temp, 2)
        min_temp = round(min(temp), 2) # assigned to global min_temp
        max_temp = round(max(temp), 2)
        range_temp = max_temp - min_temp

    return render_template("tempChart.html", temp=temp, time=time, label=label, name=name, mean=average_temp, max_temp=max_temp, min_temp=min_temp, range_temp=range_temp)



@app.route("/phChart/<x>")
def powerOfHydrogen(x):
    print(">>> ph page running ...")
    # connecting to datebase
    con = psycopg2.connect("dbname='IotIrrigation' user='postgres' host='localhost' password='12345678'")
    cursor = con.cursor()

    # data processing for an hour 
    if x == '1h':
        name = '1 Hour'
        label = 'Minute'

        # selecting ph data
        cursor.execute(" SELECT time, ph FROM ( SELECT * from SensorRecords ORDER BY id DESC LIMIT 120 )as x order by id asc ") 
        data = cursor.fetchall()
        # print(data)

        # emptying list 
        del time[:]
        del ph[:]

        # data extraction
        for datum in data:
            # print(datum)
            # extracting ph data
            datum_float = float(datum[1])
            ph.append(datum_float)
            # extracting minutes and seconds
            t = str(datum[0])[14:]
            time.append(t)
        
        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    # data processing for day 
    if x == '1d':
        name = '1 Day'
        label = 'Hour'

        # selecting ph data
        cursor.execute(" SELECT time, ph FROM SensorRecords ORDER BY id ASC LIMIT 2880 ") 
        data = cursor.fetchall()

        # emptying list 
        del time[:]
        del ph[:]

        # data extraction
        for datum in data:
            # print(datum)
            # extracting ph data
            datum_float = float(datum[1])
            ph.append(datum_float)
            # extracting minutes and seconds
            t = str(datum[0])[11:16]
            time.append(t)

        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )


     # weekly data processing ,,,,,

    if x == '1w':
        name = '1 Week'
        label = 'Day'

        # fetching data from database
        cursor.execute(" SELECT time, ph FROM SensorRecords ORDER BY id ASC LIMIT 20160") 
        data = cursor.fetchall()
        
        # converting timestamp from database to day in string like Mon, Tue
        def date_to_day(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%a"))

        # emptying time and ph container list
        del time[:]
        del ph[:]

        # retrieving weekly time and ph from database data
        for datum in data:
            # collecting ph
            # print(datum)
            datum_float = float(datum[1])   # ph data in float
            ph.append(datum_float)        # pushing to ph list

            # string day processing from full timestamp
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # converting full_date to day_string function defined 
            current_day = date_to_day(year, month, day)
            time.append(current_day)
            
        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    
     # monthly data processing

    if x == '1m':
        name = '1 Month'
        label = 'Month-Date'

        # fetching data from database.....change number of data to fetch
        cursor.execute(" SELECT time, ph FROM SensorRecords ORDER BY id ASC LIMIT 87600") 
        data = cursor.fetchall()

        # emptying list
        del time[:]
        del ph[:]

        # extracting monthly time and ph data to empty list
        for datum in data:
            # collecting ph
            # print(datum)
            datum_float = float(datum[1])   # ph data to float
            ph.append(datum_float)       

            # extracting month from full timestamp
            tm = str(datum[0])[5:10]
            time.append(tm)
        
         # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )


    # yearly data processing

    if x == '1y':
        name = '1 Year'
        label = 'Month'

        cursor.execute(" SELECT time, ph FROM SensorRecords ORDER BY id ASC LIMIT 1051333") 
        data = cursor.fetchall()

         # retreiving month in string from timestamp of database to get sth like January, Febuary
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname

        # emptying
        del time[:]
        del ph[:]

        # retrieving monthly time and ph to emptied list above
        for datum in data:
            # collecting ph
            datum_float = float(datum[1])   # temp data in float
            ph.append(datum_float)        # pushing to temp list

            # string month processing from full date timestamp
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])

            # using full_date to day_string function to get month in string 
            current_month = string_month_from_full_date(year, month, day)
            time.append(current_month)

        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    
    # all data processing

    if x == 'all':
        name = 'All'
        label = "Time"
        cursor.execute(" SELECT time, ph FROM ( SELECT * from SensorRecords ORDER BY id DESC )as x order by id asc") 
        data = cursor.fetchall()
        
        # emptying 
        del time[:]
        del ph[:]
        # retrieving monthly time and ph to emptied list
        for datum in data:
            # collecting temperature
            datum_float = float(datum[1])   # ph data in float
            ph.append(datum_float)        # pushing to ph list

            # string month processing from full date timestamp
            tm = str(datum[0])[:7]
            time.append(tm)
            
        # analysis
        average_ph = round(stat.mean(ph), 2)
        min_ph = round(min(ph), 2)
        max_ph = round(max(ph), 2)
        range_ph = float( round((max_ph - min_ph), 2) )

    return render_template("phChart.html", ph=ph, time=time, label=label, name=name, average_ph=average_ph, min_ph=min_ph, max_ph=max_ph, range_ph=range_ph)



@app.route("/moistChart/<x>")
def moist(x):
    print(">>> moisture page running ...")
    con = psycopg2.connect("dbname='IotIrrigation' user='postgres' host='localhost' password='12345678'")
    cursor = con.cursor()
    if x == '1h':
        name = '1 Hour'
        label = 'Minute'
        cursor.execute(" SELECT time, moisture FROM ( SELECT * from SensorRecords ORDER BY id DESC LIMIT 120 ) as x order by id asc ") 
        data = cursor.fetchall()
        del time[:]
        del moisture[:]
        for datum in data:
            datum_float = float(datum[1])
            moisture.append(datum_float)
            t = str(datum[0])[14:]
            time.append(t)
        average_moisture = round(stat.mean(moisture), 2)
        min_moisture = round(min(moisture), 2)
        max_moisture= round(max(moisture), 2)
        range_moisture = float( round((max_moisture - min_moisture), 2) )
        print("range", range_moisture)
    
    # data processing for day 
    if x == '1d':
        name = '1 Day'
        label = 'Hour'
        cursor.execute(" SELECT time, moisture FROM SensorRecords ORDER BY id ASC LIMIT 2880 ") 
        data = cursor.fetchall()
        del time[:]
        del moisture[:]
        # appending data to emptied list
        for datum in data:
            datum_float = float(datum[1])
            moisture.append(datum_float)
            t = str(datum[0])[11:16]
            time.append(t)
        # to 2 decimal places
        average_moisture = round( stat.mean(moisture) , 2)
        min_moisture = round(min(moisture), 2)
        max_moisture = round(max(moisture), 2)
        range_moisture = float( round((max_moisture - min_moisture), 2) )

    if x == '1w':
        name = '1 Week'
        label = 'Day'
        cursor.execute(" SELECT time, moisture FROM SensorRecords ORDER BY id ASC LIMIT 20160") 
        data = cursor.fetchall()
        def date_to_day(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%a"))
        del time[:]
        del moisture[:]
        for datum in data:
            # print(datum)
            datum_float = float(datum[1])   # ph data in float
            moisture.append(datum_float)        # pushing to ph list
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])
            current_day = date_to_day(year, month, day)
            time.append(current_day)
        average_moisture = round( stat.mean(moisture) , 2)
        min_moisture = round(min(moisture), 2)
        max_moisture = round(max(moisture), 2)
        range_moisture = float( round((max_moisture - min_moisture), 2) )

    if x == '1m':
        name = '1 Month'
        label = 'Month-Date'
        cursor.execute(" SELECT time, moisture FROM SensorRecords ORDER BY id ASC LIMIT 87600") 
        data = cursor.fetchall()
        del time[:]
        del moisture[:]
        for datum in data:
            datum_float = float(datum[1])   # ph data to float
            moisture.append(datum_float)       
            tm = str(datum[0])[5:10]
            time.append(tm)
        average_moisture = round( stat.mean(moisture) , 2)
        min_moisture = round(min(moisture), 2)
        max_moisture = round(max(moisture), 2)
        range_moisture = float( round((max_moisture - min_moisture), 2) )
    
    if x == '1y':
        name = '1 Year'
        label = 'Month'
        cursor.execute(" SELECT time, moisture FROM SensorRecords ORDER BY id ASC LIMIT 1051333") 
        data = cursor.fetchall()
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname
        del time[:]
        del moisture[:]
        for datum in data:
            datum_float = float(datum[1])   # temp data in float
            moisture.append(datum_float)        # pushing to temp list
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])
            current_month = string_month_from_full_date(year, month, day)
            time.append(current_month)
        average_moisture = round( stat.mean(moisture) , 2)
        min_moisture = round(min(moisture), 2)
        max_moisture = round(max(moisture), 2)
        range_moisture = float( round((max_moisture - min_moisture), 2) )

    if x == 'all':
        name = 'All'
        label = "Time"
        cursor.execute(" SELECT time, moisture FROM ( SELECT * from SensorRecords ORDER BY id DESC )as x order by id asc") 
        data = cursor.fetchall()
        del time[:]
        del moisture[:]
        for datum in data:
            datum_float = float(datum[1])   # ph data in float
            moisture.append(datum_float)        # pushing to ph list
            tm = str(datum[0])[:7]
            time.append(tm)
        average_moisture = round( stat.mean(moisture) , 2)
        min_moisture = round(min(moisture), 2)
        max_moisture = round(max(moisture), 2)
        range_moisture = float( round((max_moisture - min_moisture), 2) )
    
    return render_template("moistChart.html", moisture=moisture, time=time, label=label, name=name, average_moisture=average_moisture, min_moisture=min_moisture, max_moisture=max_moisture, range_moisture=range_moisture)



@app.route("/waterusedChart/<x>")
def wateramount(x):
    print(">>> waterused page running ...")
    con = psycopg2.connect("dbname='IotIrrigation' user='postgres' host='localhost' password='12345678'")
    cursor = con.cursor()
    if x == '1h':
        name = '1 Hour'
        label = 'Minute'
        cursor.execute(" SELECT time, water_used FROM ( SELECT * from SensorRecords ORDER BY id DESC LIMIT 120 ) as x order by id asc ") 
        data = cursor.fetchall()
        del time[:]
        del water_used[:]
        for datum in data:
            datum_float = float(datum[1])
            water_used.append(datum_float)
            t = str(datum[0])[14:]
            time.append(t)
        average_water_used = round(stat.mean(water_used), 2)
        min_water_used = round(min(water_used), 2)
        max_water_used = round(max(water_used), 2)
        range_water_used = float( round((max_water_used - min_water_used), 2) )
    
    # data processing for day 
    if x == '1d':
        name = '1 Day'
        label = 'Hour'
        cursor.execute(" SELECT time, water_used FROM SensorRecords ORDER BY id ASC LIMIT 2880 ") 
        data = cursor.fetchall()
        del time[:]
        del water_used[:]
        for datum in data:
            datum_float = float(datum[1])
            water_used.append(datum_float)
            t = str(datum[0])[11:16]
            time.append(t)
        average_water_used = round( stat.mean(water_used) , 2)
        min_water_used = round(min(water_used), 2)
        max_water_used = round(max(water_used), 2)
        range_water_used = float( round((max_water_used - min_water_used), 2) )

    if x == '1w':
        name = '1 Week'
        label = 'Day'
        cursor.execute(" SELECT time, water_used FROM SensorRecords ORDER BY id ASC LIMIT 20160") 
        data = cursor.fetchall()
        def date_to_day(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%a"))
        del time[:]
        del water_used[:]
        for datum in data:
            # print(datum)
            datum_float = float(datum[1])   # ph data in float
            water_used.append(datum_float)        # pushing to ph list
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])
            current_day = date_to_day(year, month, day)
            time.append(current_day)
        average_water_used = round( stat.mean(water_used) , 2)
        min_water_used = round(min(water_used), 2)
        max_water_used = round(max(water_used), 2)
        range_water_used = float( round((max_water_used - min_water_used), 2) )

    if x == '1m':
        name = '1 Month'
        label = 'Month-Date'
        cursor.execute(" SELECT time, water_used FROM SensorRecords ORDER BY id ASC LIMIT 87600") 
        data = cursor.fetchall()
        del time[:]
        del water_used[:]
        for datum in data:
            datum_float = float(datum[1])   # ph data to float
            water_used.append(datum_float)       
            tm = str(datum[0])[5:10]
            time.append(tm)
        average_water_used = round( stat.mean(water_used) , 2)
        min_water_used = round(min(water_used), 2)
        max_water_used = round(max(water_used), 2)
        range_water_used = float( round((max_water_used - min_water_used), 2) )
    
    if x == '1y':
        name = '1 Year'
        label = 'Month'
        cursor.execute(" SELECT time, water_used FROM SensorRecords ORDER BY id ASC LIMIT 1051333") 
        data = cursor.fetchall()
        def string_month_from_full_date(year, month, day):
            time = datetime.datetime(year, month, day)
            return (time.strftime("%b")) # %B for fullname
        del time[:]
        del water_used[:]
        for datum in data:
            datum_float = float(datum[1])   # temp data in float
            water_used.append(datum_float)        # pushing to temp list
            tm = str(datum[0])[:10]
            tm_split = tm.split("-")
            year = int(tm_split[0])
            month = int(tm_split[1])
            day = int(tm_split[2])
            current_month = string_month_from_full_date(year, month, day)
            time.append(current_month)
        average_water_used = round( stat.mean(water_used) , 2)
        min_water_used = round(min(water_used), 2)
        max_water_used = round(max(water_used), 2)
        range_water_used = float( round((max_water_used - min_water_used), 2) )

    if x == 'all':
        name = 'All'
        label = "Time"
        cursor.execute(" SELECT time, water_used FROM ( SELECT * from SensorRecords ORDER BY id DESC )as x order by id asc") 
        data = cursor.fetchall()
        del time[:]
        del water_used[:]
        for datum in data:
            datum_float = float(datum[1])   # ph data in float
            water_used.append(datum_float)        # pushing to ph list
            tm = str(datum[0])[:7]
            time.append(tm)
        average_water_used = round( stat.mean(water_used) , 2)
        min_water_used = round(min(water_used), 2)
        max_water_used = round(max(water_used), 2)
        range_water_used = float( round((max_water_used - min_water_used), 2) )
    
    return render_template("waterusedChart.html", water_used=water_used, time=time, label=label, name=name, average_water_used=average_water_used, min_water_used=min_water_used, max_water_used=max_water_used, range_water_used=range_water_used)










@app.route("/dashboard", methods=["GET"])
def dashboard():
    print(">>> dashboard running ...")
    
    con = psycopg2.connect("dbname='IotIrrigation' user='postgres' host='localhost' password='12345678'")
    cursor = con.cursor()

    # selecting current hour data ...ie, 120 for every 30 seconds of posting
    cursor.execute(" SELECT * FROM SensorRecords ORDER BY id DESC LIMIT 120") 
    data = cursor.fetchall()
    data = list(data)

    print(".........Page refreshed at", datetime.datetime.now())

    # data collector
    temp_data = []
    moisture_data = []
    ph_data = []
    waterused_data = []

    # collecting individual data to collectors
    for row in data:
        temp_data.append(row[2])   
        moisture_data.append(row[5])
        ph_data.append(row[4])
        waterused_data.append(row[3])

    # last value added to database...current data recorded 
    last_temp_data = temp_data[0]
    last_moisture_data = moisture_data[0]
    last_ph_data = ph_data[0]
    last_waterused_data = waterused_data[0]


    # message toasting 
    if (last_temp_data < 24) | (last_temp_data > 30):
        flash("Abnormal Water Temperature", 'warning')
    if (last_moisture_data < 70) | (last_moisture_data > 81):
        flash("Abnormal Water moisture", 'warning')
    if (last_ph_data < 6) | (last_ph_data > 7):
        flash("Abnormal Water pH", 'warning')
    

    # current sum of 1hour data rounded to 2dp
    current_temp_sum = round(sum(temp_data), 2)
    current_moisture_sum = round(sum(moisture_data), 2)
    current_ph_sum = round( sum(ph_data), 2 )
    current_waterused_sum = round( sum(waterused_data), 2)  
    
    # fetching 240 data from db to extract the penultimate 120 data to calculate percentage change
    cursor.execute(" SELECT * FROM SensorRecords ORDER BY id DESC LIMIT 240") 
    data = list(cursor.fetchall())

    # collecting individual data
    prev_temp_data = []  # collecting temp values
    prev_moisture_data = []
    prev_ph_data = []
    prev_waterused_data = []
    for row in data:
        prev_temp_data.append(row[2])
        prev_moisture_data.append(row[5])
        prev_ph_data.append(row[4])
        prev_waterused_data.append(row[3])

    # slicing for immediate previous 120 data 
    prev_temp_data = prev_temp_data[120:240]
    prev_temp_sum = round( sum(prev_temp_data), 2 )

    prev_moisture_data = prev_moisture_data[120:240]
    prev_moisture_sum = round( sum(prev_moisture_data), 2 )

    prev_ph_data = prev_ph_data[120:240]
    prev_ph_sum = round( sum(prev_ph_data), 2 )

    prev_waterused_data = prev_waterused_data[120:240]
    prev_waterused_sum = round( sum(prev_waterused_data), 2 )

    # temp, getting the percentage change
    temp_change = prev_temp_sum - current_temp_sum
    temp_change = round(temp_change, 2)
    percentage_temp_change = (temp_change/current_temp_sum) * 100
    percentage_temp_change = round(percentage_temp_change, 1)
    
    # ph, getting the percentage change
    ph_change = prev_ph_sum - current_ph_sum
    ph_change = round(ph_change, 2)
    percentage_ph_change = (ph_change/current_ph_sum) * 100
    percentage_ph_change = round(percentage_ph_change,1)

    # turbidity, getting the percentage change
    moisture_change = prev_moisture_sum - current_moisture_sum
    moisture_change = round(moisture_change, 2)
    percentage_moisture_change = (moisture_change/current_moisture_sum) * 100
    percentage_moisture_change = round(percentage_moisture_change,1)

    # waterlevel, getting the percentage change
    waterused_change = prev_waterused_sum - current_waterused_sum
    waterused_change = round(waterused_change, 2)
    percentage_waterused_change = (waterused_change/current_waterused_sum) * 100
    percentage_waterused_change = round(percentage_waterused_change,1)


    # notification toast 
    # flash("Not So OK", 'error')

    return render_template("dashboard.html", data=data, percentage_temp_change=percentage_temp_change, percentage_ph_change=percentage_ph_change, percentage_moisture_change=percentage_moisture_change, percentage_waterused_change=percentage_waterused_change, temp_change=temp_change, ph_change=ph_change, moisture_change=moisture_change, waterused_change=waterused_change, last_temp_data=last_temp_data, last_ph_data=last_ph_data, last_moisture_data=last_moisture_data, last_waterused_data=last_waterused_data)




@app.route("/download/<prop>")
def get_CSV(prop):
    print(">>> csv file downloaded")

    if prop == 'temperature':
        # prepare data in csv format
        generator.generate_csv_file(prop)

        # opens, reads, closes csv file for download 
        with open(f'data/IoTIrrigationSystem_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        # routes function returning the file download
        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=IoTIrrigationSystem_%s.csv" %prop}
        )
    

    if prop == 'moisture':
        generator.generate_csv_file(prop)
        with open(f'data/IoTIrrigationSystem_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=IoTIrrigationSystem_%s.csv" %prop}
        )


    if prop == 'ph':
        generator.generate_csv_file(prop)
        with open(f'data/IoTIrrigationSystem_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=IoTIrrigationSystem_%s.csv" %prop}
        )
    

    if prop == 'water_used':
        generator.generate_csv_file(prop)
        with open(f'data/IoTIrrigationSystem_{prop}_data.csv', 'r') as csv_file:
            csv_reader = csv_file.read().encode('latin-1')
        csv_file.close()

        return Response(
            csv_reader,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=IoTIrrigationSystem_%s.csv" %prop}
        )
       


# main function
if  __name__ == "__main__":
    try:
        # using local ip address and auto pick up changes
        app.run(debug=True, port=5000, use_reloader=False)  # host='10.10.65.5', port=5000

        

        # using static ip
        # app.run(debug=True, host='192.168.43.110 ', port=5050)   # setting your own ip

    except Exception as rerun:
        print(">>> Failed to run main program : ",rerun)
