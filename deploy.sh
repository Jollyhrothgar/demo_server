#!/bin/bash

#Kill all main.py running on the system
./kill.sh

#Iterate over every directory in demos area
for demo in `find demos -maxdepth 2 | grep 'main.py'`; do
	python $demo &
done

# add a means to spawn virtualenvs later. The previous means would not have worked.
