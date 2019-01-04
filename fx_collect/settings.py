import os
# Directorys
BASE_DIR = os.getcwd()
JSON_DIR = BASE_DIR + '/json_files/'
LOGS_DIR = BASE_DIR + '/logs/'

# Limit collection only to these timeframes. 
# If it is empty, all timeframes are collected.
# FXCM API currently supports these timeframes: ['m1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H4', 'H8', 'D1', 'W1', 'M1']
COLLECT_TIMEFRAMES_ONLY = []

# Set either credentials here, or path to the file where the credentials are kept
# Credentials format: {'live'|'Demo'}:<FXCM username>:<FXCM password>
# You need to correctly specify either live or demo account, otherwise FXCM will not let you log in.
# Example: FXCM_CREDENTIALS = "Demo:D123456789:1234"
FXCM_CREDENTIALS = ""
FXCM_CREDENTIALS_FILE = ""
