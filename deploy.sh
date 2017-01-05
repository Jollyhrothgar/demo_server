#!/bin/bash
for d in */ ; do
	#if [ -d $d/venv ]
	#then
	#	echo "Found a virtual environment in $d"
	#	source venv


	if [ -f $d/main.py ]
	then
		echo "Found a main.py in $d"
		python $d/main.py &
	fi
done
