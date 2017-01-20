#!/bin/bash

#Kill all main.py running on the system
for process in `ps aux | grep '[m]ain.py' | awk '{print $2}'`; do
	echo "Killing process: $process"
	kill $process
done

#Iterate over every directory in demos area
for demo in `find demos -maxdepth 2 | grep 'main.py'`; do
	python $demo &
done

# This is a fancier version for when/if demo modules will support
# independant their own virtual environments

#for d in */ ; do
	##Find if theres a main.py in this directory
	#if [ -f $d/main.py ]
	#then
		#echo "Found a main.py in $d"

		##Check if theres a virtual environment to source before we can deploy
		#if [ -d $d/venv ]
		#then
			#echo "Found a virtual environment in $d"
			#env = true
			#source $d/venv/bin/activate
		#fi

		##Deploy!
		#python $d/main.py &

		#if [ "$env" = true ]
		#then
			#deactivate
			#unset env
		#fi
	#fi
#done
