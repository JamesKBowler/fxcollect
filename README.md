# fxcmminer v1.0

The purpose of this software is to fully automate the simultaneous collection of historical and live financial data from FXCM, then store these data in a database ready for backtesting or live execution.

### Setup
I use an ESXi server for all my virtual machines, however this will run on any hypervisor and most hardware.

Specification:  
   2x CPUs  
   4GB RAM  
   100GB SSD/HDD (for testing hard drive is fine)  

Total drive usage for the database (excluding OS etc) is 41GB as of 29/04/2017

I am using on Ubuntu Server 16.04 (without GUI) for testing, however this will run on most Linux OS with/without GUI.

1. First install all dependencies in the requiements.txt and Python 2.7

2. Install MariaDB 10.x  
  https://mariadb.org/download/

3. Setup MariaDB to allow the user 'sec_master' to access the database with read and write permissions.

   $ mysql -u root -p  

   mysql> CREATE USER 'sec_master'@'localhost' IDENTIFIED BY 'password';  
   mysql> GRANT ALL PRIVILEGES ON *.* TO 'sec_master'@'localhost';  
   mysql> FLUSH PRIVILEGES;  

   (optional)  
   $ sudo service mysql restart  

4. Download forexconnect and follow instructions.  
 https://github.com/JamesKBowler/python-forexconnect  

5. Download this repository and place in a convenient location

6. Create a logs folder in the root directory  
 $ mkdir ~/fxcmminer/fxcmminer_v1.0/logs
 
7. Set the system time zone to EST, this is important as all data on FXCM servers are stored in EST.  
 $ sudo timedatectl set-timezone EST

8. To start the process just execute:  
 $ python ~/fxcmminer/fxcmminer_v1.0/engine.py  

##### All FXCM data will take about 30 hours to download.

If you need assistance setting this up or find any bugs, please report using the Issue section.

### TODO:

1. Prioritize queue so that Live data is written to database before historical.

2. Improve logging

3. Add auto offer removal to the fxscout

4. Clean up code!

### Code Explanation

#### Scout

The process of collecting data is started by executing the engine.py script. This in turn will start the fxscout.py, who's primary job is to scout FXCM for currently tradable instruments (also know as 'offers'). Once the Scout has found 'offers' available, it will contact FXCM for the .xml catalogue and make a local copy to be accessed later by fxcmminer. If FXCM add another 'offer' the Scout will then make a new local copy of the catalogue. 

The scout will continue checking FXCM for the entire duration whilst the program is running, and will only place an 'OFFER' event in the events queue on system startup or if a new 'offer' is added in the future.

#### DatabaseManager

If an 'OFFER' event is placed in the queue, the Engine class will pass the event over to the DatabaseManager located in db_manager.py. DatabaseManager will compare its local database with the offer. If the database already exists the creation is skipped, if not the corresponding database and tables for the following time frames will be created.

  {GBP/USD : ['M1','W1','D1','H8', 'H4', 'H2', 'H1','m30', 'm15', 'm5', 'm1']}

The schema is one database per offer as this will provide plenty of space for future expansion.

#### HistoricalCollector 

After a database check or creation has been carried out, a 'DBReady' event is placed into the queue, which is then passed over to the HistoricalCollector class located in historical.py .
The HistoricalCollector asks the DatabaseManager for the lastest date in the database, if this is a new offer or first time system startup, the DatabaseManager will return a date from the .xml catalogue. If the catalog does not have a corresponding date an artificial low date of 2007-01-01 00:00:00 is returned.
Now the HistoricalCollector has a starting point, it will begin to call FXCM's API and collect data. Once data is returned, a 'HISTDATA' event is created and placed in the queue, which in turn will be passed to the DatabaseManager and written to the database.
After all historical data has been collected for the offer, a 'GETLIVE' event is placed into the queue and the HistoricalCollector process will exit.

#### LiveDataMiner 

On receipt of the 'GETLIVE' event, LiveDataMiner located in live.py, will continue to collect live data using a series of time based events from apscheduler. Each event from apscheduler fires off a data collection sequence. Once data is collected a 'LIVEDATA' event is created and placed in the queue for the DatabaseManager and written to the database.

#### Other classes 

TimeDelta will provide a range in minutes for each time frame, that will not exceed to 300 bars (data points). This is because the maximum bars return for any one API call to FXCM is 300.
Using the information from TimeDelta, DateRange will provide a date block which is used when calling the API. At the moment this is the only way I could exclude calling for data at the weekends whilst FXCM is closed, and due to the nature of the foreign exchange, holidays are not equal in all countries.

# License Terms  

Copyright (c) 2017 James K Bowler  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  

# Forex Trading Disclaimer  

Trading foreign exchange on margin carries a high level of risk, and may not be suitable for all investors. Past performance is not indicative of future results. The high degree of leverage can work against you as well as for you. Before deciding to invest in foreign exchange you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with foreign exchange trading, and seek advice from an independent financial advisor if you have any doubts.
