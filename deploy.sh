#!/bin/bash

#Kill all main.py running on the system
kill $(ps aux| grep '[m]ain.py' | awk '{print $2}')

#Iterate over every directory
for d in */ ; do
	#Find if theres a main.py in this directory
	if [ -f $d/main.py ]
	then
		echo "Found a main.py in $d"

		#Check if theres a virtual environment to source before we can deploy
		if [ -d $d/venv ]
		then
			echo "Found a virtual environment in $d"
			env = true
			source $d/venv/bin/activate
		fi

		#Deploy!
		python $d/main.py &

		if [ "$env" = true ]
		then
			deactivate
			unset env
		fi
	fi
done
