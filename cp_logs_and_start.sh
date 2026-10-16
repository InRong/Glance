#!/bin/sh
#
# Copy the log file
logdir="home/alan/Glance/logs"
if [ -f ${logdir}/$1.log ]; then
	cp ${logdir}/$1.log ${logdir}/$1.log.save
fi
# Start the app
/home/alan/Glance/start_Glance.sh $1 $2

