# How to Use This Application
Timetracker is a python script with a GUI that helps you track how you spend your time by creating entries that can be imported into other tools (e.g., Google Calendar). It allows you to log time against specific projects and maintain consistent time tracking throughout your workday.

# Setup
## Run the following commands to make sure you have the necessary libraries:
* `pip install PySide6`
* `pip install schedule`
  
## Move to an accessible location to create a shortcut and mark executable
1. `mkdir -p ~/bin`
2. `cp /path/to/file/run_timetracker.sh ~/bin/timetracker`
3. `chmod +x ~/bin/timetracker`

## tell your bash profile to look for this executable script:
1. `open -t ~/.bash_profile`
2. add this to the end of the bash profile: `export PATH="$HOME/bin:$PATH"`
3. `source ~/.bash_profile`
4. `sudo mdutil -E /`

# Running the Application
You can now run the script from Spotlight: timetracker.command

# Features
## Create a single timetracking entry
* Selects a project from the predefined list
* Sets the start time (defaults to current time)
* Creates a 30-minute entry
* Adds the entry to a CSV file
* Start the scheduler

## Scheduled prompts
* Automatically prompts for entries every 30 minutes from 9:30 AM to 5:30 PM
* Only runs on business days (Monday-Friday)
* Saves all entries to the CSV file

## Display CSV import instructions
Shows step-by-step instructions for importing the CSV file into Google Calendar
