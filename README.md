# How to use this script
Timetracker is a python script with a GUI that helps you track how you spend your time by creating entries that can be imported into other tools (e.g., Google Calendar). It allows you to log time against specific projects and maintain consistent time tracking throughout your workday.

# Setting up and running the script
1. Download the repo
2. Run the following steps to create a local folder to run the script from, store the CSV to, etc. and enable to script to be run:
    1. Create the folder: `mkdir -p ~/Documents/Timetracker`
    2. Copy the bash into a shell command: `cp ~/Downloads/timetracker-main/run_timetracker.sh ~/Documents/Timetracker/timetracker.command`
    3. Copy the script into the same folder: `cp ~/Downloads/timetracker-main/timetracking_csv.py ~/Documents/Timetracker/timetracking_csv.py`
    4. Make it executable: `chmod +x ~/Documents/Timetracker/timetracker.command`

# Running the script
At this point the script should be able to be run. Use spotlight to start the process, open it with finder, or run it straight from the terminal.

## Initial project list setup
Configure the list of pre-defined projects that you want to track time against. Supply at least one project and you'll be ready to go! You can always go back and edit this to add others if you find the need. No need to list out every single project - the dialog to add time will allow an "Other" option with free text for those things that come up irregularly.

## Troubleshooting
If you're running into issues running the program, make sure these libraries are installed on your machine. At the terminal use the following commands:
* `pip3 install --upgrade PySide6`
* `pip3 install --upgrade schedule`

# Features
## Create a single timetracking entry
* Selects a project from the predefined list
* Sets the start time (defaults to current time)
* Creates a 30-minute entry
* Adds the entry to a CSV file
* Start the scheduler

## Scheduled timetracking prompts
* Same as the above, but automatically prompts for entries every 30 minutes from 9:30 AM to 5:30 PM
* Only runs on business days (Monday-Friday)
* Saves all entries to the CSV file

## Manage projects
Creates a persisted list of pre-defined projects you'll log against

## Display CSV import instructions
Shows step-by-step instructions for importing the CSV file into Google Calendar

# Issues? This was a vibecoded project after all...
Please feel free to contact me (bryndavis) if you have issues running this
