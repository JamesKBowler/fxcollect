# fxcmminer v1.0

The purpose of this software is to fully automate the collection of historical and live financial data from FXCM, then store these data in a database ready for back testing or live execution.

Setup
I use an ESXi server for all my virtual machines, however this will run on any hypervisor.

Hardware or Virtual machine:
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
mkdir ~/fxcmminer/fxcmminer_v1.0/logs

To start the process just execute:
python ~/fxcmminer/fxcmminer_v1.0/engine.py

This will take about 30 hours to download.

If you need assistance setting this up or find any bugs, please report using the Issue section.

+++++
TODO:
+++++

1. Prioritize queue so that Live data is written to database before historical.

2. Improve logging

2. Clean up code!
