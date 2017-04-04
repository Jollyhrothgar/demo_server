#!/bin/bash

#Kill all main.py running on the system
for process in `ps aux | grep '[m]ain.py' | awk '{print $2}'`; do
	echo "Killing process: $process"
	kill $process
done
