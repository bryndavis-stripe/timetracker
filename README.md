# How to Use This Application
# Setup
# Save the script as timetracking_csv.py
# Run the following commands:
# # pip install PySide6
# # pip install schedule
#
# Move to an accessible location to create a shortcut and mark executable
# # mkdir -p ~/bin
# # cp /path/to/file/run_timetracker.sh ~/bin/timetracker
# # chmod +x ~/bin/timetracker
#
# tell your bash profile to look for this executable script:
# # open -t ~/.bash_profile
# # add this to the end of the bash profile: export PATH="$HOME/bin:$PATH"
# # source ~/.bash_profile
# # sudo mdutil -E /
#
# Running the Application
# # You can now run the script : timetracker
# ​
# Features
# # Create a single timetracking entry
# # # Selects a project from the predefined list
# # # Sets the start time (defaults to current time)
# # # Creates a 30-minute entry
# # # Adds the entry to a CSV file
# # # Start the scheduler
# 
# # Automatically prompts for entries every 30 minutes from 9:30 AM to 5:30 PM
# # # Only runs on business days (Monday-Friday)
# # # Saves all entries to the CSV file
# # # Display CSV import instructions
# 
# Shows step-by-step instructions for importing the CSV file into Google Calendar
# # CSV File Format
# # # The script creates a file named timetracking_entries.csv with the following columns:
# # #  
# # #  Subject (e.g., "Timetracking: Figma")
# # #  Start Date (YYYY-MM-DD)
# # #  Start Time (HH:MM)
# # #  End Date (YYYY-MM-DD)
# # #  End Time (HH:MM)
# # #  Description
# # #  This format is compatible with Google Calendar's import feature.
# 
# # Importing to Google Calendar
# # #  Go to calendar.google.com
# # #  Click on the gear icon (Settings) in the top-right corner
# # #  Select 'Settings'
# # #  In the left sidebar, click 'Import & export'
# # #  Click 'Select file from your computer' and select your CSV file
# # #  Choose the calendar to import events to
# # #  Click 'Import'