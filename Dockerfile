FROM ubuntu:18.04
# Based on instructions in readme.md
#	and https://github.com/JamesKBowler/python-forexconnect/tree/python3-forexconnect
    
RUN apt-get -y update && apt-get -y install python3 python3-pip \
    python3-numpy python3-pymysql mariadb-server mariadb-client git \
    build-essential python3-dev libboost-log-dev libboost-date-time-dev \
    libboost-python-dev libtool m4 automake autogen checkinstall wget \
    python3-termcolor sudo libcurl4-gnutls-dev libarchive-dev cmake gosu
   
RUN pip3 install cprint pytz ipython

RUN adduser --disabled-password --gecos "" nonroot



ARG WITH_PHPMYADMIN=0
ENV WITH_PHPMYADMIN=$WITH_PHPMYADMIN

RUN if [ "$WITH_PHPMYADMIN" -gt "0" ] ; then \
		export DEBIAN_FRONTEND=noninteractive; \
		echo "phpmyadmin phpmyadmin/dbconfig-install boolean false" | debconf-set-selections; \
		echo "phpmyadmin phpmyadmin/reconfigure-webserver multiselect apache2" | debconf-set-selections; \
		apt-get -q -y install phpmyadmin; \
	fi


# --- Install libuv

RUN wget https://github.com/libuv/libuv/archive/v1.19.1/libuv-1.19.1.tar.gz && \
	tar -xvzf libuv-1.19.1.tar.gz && \
	cd libuv-1.19.1/ && \
	sh autogen.sh  && \
	./configure --prefix=/usr --disable-static && \
	make && \
	sudo checkinstall

# --- Install libarchive

#  -> Using distribution packages
#RUN wget http://www.libarchive.org/downloads/libarchive-3.3.2.tar.gz && \
#	tar -xvzf libarchive-3.3.2.tar.gz && \
#	cd libarchive-3.3.2/ && \
#	./configure --prefix=/usr --disable-static && \
#	make && \
#	sudo checkinstall
	
# --- Install curl

#  -> Using distribution packages

# --- Installing boost

#  -> Using distribution packages, Bionic is already at 1.65.
RUN apt-get -y install libboost-all-dev

# --- Install python3-forexconnect

RUN cd /home/nonroot; \
	echo "export BOOST_ROOT=/usr" >> .profile; \
	echo "export BOOST_INCLUDEDIR=/usr/include/" >> .profile; \
	echo "export BOOST_LIBRARYDIR=/usr/lib/" >> .profile; \
	echo "export INCLUDE=/usr/include/boost/:\$INCLUDE" >> .profile; \
	echo "export LIBRARY_PATH=/usr/local/:\$LIBRARY_PATH" >> .profile; \
	echo "export FOREXCONNECT_ROOT=\$(pwd)/ForexConnectAPI" >> .profile; \
	echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:\$(pwd)/ForexConnectAPI/lib" >> .profile; \
	. ./.profile; \
	ldconfig

RUN cd /home/nonroot; \
	su - nonroot -c "wget http://fxcodebase.com/bin/forexconnect/1.4.1/ForexConnectAPI-1.4.1-Linux-x86_64.tar.gz && \
		tar xvf ForexConnectAPI-1.4.1-Linux-x86_64.tar.gz && \  
		mv ForexConnectAPI-1.4.1-Linux-x86_64 ForexConnectAPI && \
		git clone -b python3-forexconnect https://github.com/JamesKBowler/python-forexconnect.git && \
		cd python-forexconnect && mkdir build && cd build && \  
		cmake .. -DDEFAULT_FOREX_URL='http://www.fxcorporate.com/Hosts.jsp' " && \
	cd python-forexconnect/build && \
	make install  

# --- Database setup

RUN service mysql start && \
	echo 	"CREATE USER 'sec_master'@'localhost' IDENTIFIED BY 'password';  \
			GRANT ALL PRIVILEGES ON *.* TO 'sec_master'@'localhost';  \
			FLUSH PRIVILEGES; \
			set global max_connections = 1000; " | mysql -uroot

RUN echo "127.0.0.1:sec_master:password" > /home/nonroot/.database_sec_master_credentials; \
	chown nonroot:nonroot /home/nonroot/.database_sec_master_credentials


COPY . /home/nonroot/fxcollect/

RUN chown -R nonroot:nonroot /home/nonroot; chmod +x /home/nonroot/fxcollect/runMainDocker.sh;

ENTRYPOINT ["/home/nonroot/fxcollect/runMainDocker.sh"] 
