# How to Use This Script
Timetracker is a python script with a GUI that helps you track how you spend your time by creating entries that can be imported into other tools (e.g., Google Calendar). It allows you to log time against specific projects and maintain consistent time tracking throughout your workday.

# Running the Script
You can also run the bash file, but you can also run the script from Spotlight using timetracker.command

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
