#!/usr/bin/env bash

# Script to run the python executable inside the container, cleaning up afterwards, passing down UNIX signals for graceful shutdown
# https://unix.stackexchange.com/questions/146756/forward-sigterm-to-child-in-bash

_term() {
	echo "Caught SIGTERM signal!"
	kill -TERM "$PID" 2>/dev/null
}
trap _term SIGTERM SIGINT

###
### Starting up services
###
service mysql start
if [ "$WITH_PHPMYADMIN" -gt "0" ]; then
	service apache2 start
fi
cd /home/nonroot/fxcollect
export LD_LIBRARY_PATH=/home/nonroot/ForexConnectAPI/lib/:/usr/local/lib/:\$LD_LIBRARY_PATH

	gosu nonroot python3 /home/nonroot/fxcollect/main.py & 

PID=$!
wait $PID
trap - SIGTERM SIGINT
wait $PID
EXIT_STATUS=$?

###
### Cleaning up services
###
service mysql stop
if [ "$WITH_PHPMYADMIN" -gt "0" ]; then
	service apache2 stop
fi
