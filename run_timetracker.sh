#!/bin/bash

# Create Timetracker folder if it doesn't exist
if [ ! -d ~/Documents/Timetracker ]; then
    mkdir -p ~/Documents/Timetracker
    echo "Created Timetracker directory: ~/Documents/Timetracker"
fi

# Change to the Timetracker directory
cd ~/Documents/Timetracker
echo "Changed to directory: $(pwd)"

# Run the time tracking Python script with full path
echo "Starting time tracking script..."
python3 ~/Documents/Timetracker/timetracking_csv.py

# Exit with the same status code as the Python script
exit $?