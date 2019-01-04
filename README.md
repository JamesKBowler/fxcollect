# fxcollect

The purpose of 'fxcollect' is to automate the collection of historical and live financial  
time series data from FXCM, then store these data in a MariaDB database ready for backtesting  
or live execution.  

### Quick Setup (using docker)
You can use the provided dockerfile to quickly and painlessly setup the application. It has been 
tested on a debian-based x86_64 distribution, but will likely work on many others. 

 1. Modify `settings.py` to at least add your FXCM login credentials.
 2. Modify `main.py` to adjust which symbols will be collected. 
 3. Browse into the top directory of the repository and build the docker container:
 
``` 
$ cd fxcollect 
$ docker build .
```
Or you can use the additional `WITH_PHPMYADMIN` argument to build container with phpmyadmin, to be able to easily
inspect the data right from the container:

    $ docker build --build-arg WITH_PHPMYADMIN=1 .
    
 4. Run the container, optionally forward ports to browse using phpmyadmin.
```
$ docker run -p 127.0.0.1:8080:80/tcp -it <built-image-id>
```
    

### Manual Setup
Specification: 
 - Ubuntu Server 16.04  
 - Python 3.x  
 - 2x CPUs  
 - 4GB RAM, but 2GB will work if tracking a few offers.  
 - 100GB SSD/HDD (for testing hard drive is fine)  
 59 instruments = 41GB as of 29/04/2017  
 
 1. Install dependencies
  - numpy  
  - pymysql  
  - cprint  
  - pytz 
  - termcolor 
 
 2. Install MariaDB 10.x  
   https://mariadb.org/download/
 
 3. Setup MariaDB to allow the user 'sec_master' to access the database with read and write permissions.  
 
    `$ mysql -u root -p`  
  
    `mysql> CREATE USER 'sec_master'@'localhost' IDENTIFIED BY 'password';`  
    `mysql> GRANT ALL PRIVILEGES ON *.* TO 'sec_master'@'localhost';`  
    `mysql> FLUSH PRIVILEGES;`  
    `mysql> set global max_connections = 1000;`  
 
    (optional)  
    `$ sudo service mysql restart`  
 
 4. Download forexconnect and follow instructions.  
     https://github.com/JamesKBowler/python-forexconnect/tree/python3-forexconnect   
 
 5. Download this repository  
  `$ git clone https://github.com/JamesKBowler/fxcollect ~/`  
 
 ##### FXCM price data stored in UTC time zone.  
 6. Set the system time zone to UTC  
  `$ sudo timedatectl set-timezone UTC`  
 
 7. Execute:  
  `$ python3 ~/fxcollect/fx_collect/main.py`  
 
##### Each instrument symbol data will take about 1 hour to download, then data will be collected at every time frame interval   
        +---------------------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+--------+
        | date                | bidopen   | bidhigh   | bidlow    | bidclose  | askopen   | askhigh   | asklow    | askclose  | volume |
        +---------------------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+--------+
        | 2017-04-27 10:01:00 | 17.294000 | 17.296000 | 17.289000 | 17.290000 | 17.340000 | 17.340000 | 17.334000 | 17.335000 |    113 |
        | 2017-04-27 10:02:00 | 17.290000 | 17.298000 | 17.285000 | 17.295000 | 17.335000 | 17.342000 | 17.330000 | 17.340000 |    114 |
        | 2017-04-27 10:03:00 | 17.295000 | 17.301000 | 17.289000 | 17.299000 | 17.340000 | 17.347000 | 17.340000 | 17.344000 |     98 |
        | 2017-04-27 10:04:00 | 17.299000 | 17.300000 | 17.286000 | 17.295000 | 17.344000 | 17.345000 | 17.330000 | 17.340000 |    124 |
        | 2017-04-27 10:05:00 | 17.295000 | 17.295000 | 17.285000 | 17.292000 | 17.340000 | 17.340000 | 17.330000 | 17.336000 |    130 |
        | 2017-04-27 10:06:00 | 17.292000 | 17.292000 | 17.279000 | 17.292000 | 17.336000 | 17.336000 | 17.328000 | 17.332000 |     65 |
        | 2017-04-27 10:07:00 | 17.292000 | 17.304000 | 17.287000 | 17.298000 | 17.332000 | 17.348000 | 17.332000 | 17.345000 |    144 |
        | 2017-04-27 10:08:00 | 17.298000 | 17.306000 | 17.297000 | 17.302000 | 17.345000 | 17.350000 | 17.343000 | 17.346000 |     96 |
        | 2017-04-27 10:09:00 | 17.302000 | 17.303000 | 17.294000 | 17.294000 | 17.346000 | 17.346000 | 17.338000 | 17.338000 |     50 |
        | 2017-04-27 10:10:00 | 17.294000 | 17.296000 | 17.281000 | 17.291000 | 17.338000 | 17.338000 | 17.328000 | 17.333000 |     50 |
        
If you need assistance setting this up or find any bugs, please report using the Issue section.  

### TODO:  
1. Update C++ code  
2. Update documentation  

# License Terms  

## Copyright (c) 2017 James K Bowler  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  

# Forex Trading Disclaimer  
Trading foreign exchange on margin carries a high level of risk, and may not be suitable for all investors. Past performance is not indicative of future results. The high degree of leverage can work against you as well as for you. Before deciding to invest in foreign exchange you should carefully consider your investment objectives, level of experience, and risk appetite. The possibility exists that you could sustain a loss of some or all of your initial investment and therefore you should not invest money that you cannot afford to lose. You should be aware of all the risks associated with foreign exchange trading, and seek advice from an independent financial advisor if you have any doubts.
