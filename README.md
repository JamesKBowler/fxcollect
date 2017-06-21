# fxcmminer v1.1

The purpose of this software is to fully automate the simultaneous collection of historical and live financial data from FXCM, then store these data in a database ready for backtesting or live execution.

### Setup
The development has been carried out on an ESXi server, however this will run on any hypervisor and most hardware.

Specification:  
   2x CPUs  
   2GB RAM  
   100GB SSD/HDD (for testing hard drive is fine)  

Total drive usage for the database (excluding OS etc) from 59 instruments, is 41GB as of 29/04/2017

Operating System:  
   Ubuntu Server 16.04 (without GUI) for testing, however this will run on most Linux OS with/without GUI.  

1. First install all dependencies in the requiements.txt and Python 2.7

2. Install MariaDB 10.x  
  https://mariadb.org/download/

3. Setup MariaDB to allow the user 'sec_master' to access the database with read and write permissions.

   `$ mysql -u root -p`  
 
   `mysql> CREATE USER 'sec_master'@'localhost' IDENTIFIED BY 'password';`  
   `mysql> GRANT ALL PRIVILEGES ON '*.*' TO 'sec_master'@'localhost';`  
   `mysql> FLUSH PRIVILEGES;`  
   `mysql> set global max_connections = 1000;`  

   (optional)  
   `$ sudo service mysql restart`  

4. Download forexconnect and follow instructions.  
 https://github.com/JamesKBowler/python-forexconnect  

5. Download this repository and place in a convenient location

6. Create a logs folder in the root directory  
 `$ mkdir ~/fxcmminer/fxcmminer_v1.0/logs`  
 
7. Set the system time zone to UTC, this is important as all data on FXCM servers are stored in UTC time zone.  
 `$ sudo timedatectl set-timezone UTC`  

8. To start the process just execute:  
 `$ python ~/fxcmminer/fxcmminer_v1.0/engine.py`  

##### All FXCM data will take about 30 hours to download.

If you need assistance setting this up or find any bugs, please report using the Issue section.

### TODO:

1. Improve logging

2. Add auto offer removal to the fxscout

# License Terms  

Copyright (c) 2017 James K Bowler  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  

# Forex Trading Disclaimer  

Trading foreign exchange on margin carries a high level of risk, and may not be suitable for all investors. Past performance is not indicative of future results. The high degree of leverage can work against you as well as for you. Before deciding to invest in foreign exchange you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with foreign exchange trading, and seek advice from an independent financial advisor if you have any doubts.
