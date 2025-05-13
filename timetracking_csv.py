import csv
import datetime
import os
import time
import sys
import json
from enum import Enum
import threading
from functools import partial
from PySide6.QtCore import Qt, QTimer, Slot, Signal, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QFont, QFontMetrics, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QLineEdit, QTimeEdit, QDialog,
    QMessageBox, QFormLayout, QFrame, QStyleFactory, QListWidget, 
    QListWidgetItem, QInputDialog, QMenu, QMenuBar, QDialogButtonBox
)
import schedule

# File to store time tracking entries and projects
CSV_FILE = 'timetracking_entries.csv'
CSV_HEADERS = ['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'Description']
PROJECTS_FILE = 'timetracking_projects.json'

def initialize_csv_file():
    """Initialize the CSV file with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
        return True
    return False

def round_time_to_half_hour(dt):
    """Round down to the nearest half-hour."""
    dt_rounded = dt.replace(minute=0, second=0, microsecond=0)
    if dt.minute >= 30:
        dt_rounded = dt_rounded.replace(minute=30)
    return dt_rounded

def is_business_day():
    """Check if today is a business day (Monday through Friday)."""
    weekday = datetime.datetime.now().weekday()
    return weekday < 5  # 0-4 are Monday to Friday

def load_projects():
    """Load projects from the projects file."""
    if os.path.exists(PROJECTS_FILE):
        try:
            with open(PROJECTS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

def save_projects(projects):
    """Save projects to the projects file."""
    with open(PROJECTS_FILE, 'w') as f:
        json.dump(projects, f)

class ProjectsDialog(QDialog):
    def __init__(self, projects, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Projects")
        self.setMinimumWidth(400)
        
        self.projects = projects.copy()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface for the projects dialog."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Manage your projects below:")
        layout.addWidget(instructions)
        
        # Projects list
        self.projects_list = QListWidget()
        self.populate_projects_list()
        layout.addWidget(self.projects_list)
        
        # Buttons for managing projects
        btn_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Project")
        self.add_button.clicked.connect(self.add_project)
        btn_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit Project")
        self.edit_button.clicked.connect(self.edit_project)
        btn_layout.addWidget(self.edit_button)
        
        self.remove_button = QPushButton("Remove Project")
        self.remove_button.clicked.connect(self.remove_project)
        btn_layout.addWidget(self.remove_button)
        
        layout.addLayout(btn_layout)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def populate_projects_list(self):
        """Populate the projects list with current projects."""
        self.projects_list.clear()
        for project in self.projects:
            self.projects_list.addItem(project)
    
    def add_project(self):
        """Add a new project."""
        project_name, ok = QInputDialog.getText(self, "Add Project", "Project name:")
        if ok and project_name.strip():
            self.projects.append(project_name.strip())
            self.populate_projects_list()
    
    def edit_project(self):
        """Edit the selected project."""
        current_item = self.projects_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a project to edit.")
            return
        
        current_text = current_item.text()
        index = self.projects.index(current_text)
        
        new_name, ok = QInputDialog.getText(
            self, "Edit Project", "Project name:", text=current_text
        )
        
        if ok and new_name.strip():
            self.projects[index] = new_name.strip()
            self.populate_projects_list()
    
    def remove_project(self):
        """Remove the selected project."""
        current_item = self.projects_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a project to remove.")
            return
        
        current_text = current_item.text()
        
        reply = QMessageBox.question(
            self, "Confirm Removal", f"Are you sure you want to remove '{current_text}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.projects.remove(current_text)
            self.populate_projects_list()
    
    def accept(self):
        """Handle dialog acceptance."""
        # Filter out any empty projects before saving
        self.projects = [p for p in self.projects if p.strip()]
        
        if not self.projects:
            QMessageBox.critical(self, "Error", "You must have at least one project.")
            return
        
        super().accept()

class TimeEntryDialog(QDialog):
    def __init__(self, projects, use_scheduler=False, parent=None):
        super().__init__(parent)
        self.use_scheduler = use_scheduler
        self.projects = projects
        self.project_name = ""
        self.start_time = None
        self.end_time = None
        
        # Get current date and time
        self.now = datetime.datetime.now()
        
        # Always round time down to nearest half hour
        self.now = round_time_to_half_hour(self.now)
            
        self.today_date = self.now.strftime("%Y-%m-%d")
        self.default_time = self.now.strftime("%H:%M")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface for the time entry dialog."""
        # Set dialog properties
        self.setWindowTitle("Create Time Tracking Entry")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Create Time Tracking Entry")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)
        
        # Date display
        date_label = QLabel(f"Date: {self.today_date}")
        main_layout.addWidget(date_label)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Form layout for input fields
        form_layout = QFormLayout()
        
        # Project selection
        self.project_combo = QComboBox()
        self.project_combo.addItems(self.projects + ['Other'])
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        form_layout.addRow("Project:", self.project_combo)
        
        # Custom project name (initially hidden)
        self.custom_project_edit = QLineEdit()
        self.custom_project_label = QLabel("Custom project name:")
        self.custom_project_label.setHidden(True)
        self.custom_project_edit.setHidden(True)
        form_layout.addRow(self.custom_project_label, self.custom_project_edit)
        
        # Time inputs
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        
        if self.use_scheduler:
            # In scheduler mode, set current time as end time and calculate start time
            current_time = self.now
            start_time = current_time - datetime.timedelta(minutes=30)
            self.start_time_edit.setTime(
                datetime.datetime.strptime(start_time.strftime("%H:%M"), "%H:%M").time()
            )
            self.end_time_edit.setTime(
                datetime.datetime.strptime(current_time.strftime("%H:%M"), "%H:%M").time()
            )
        else:
            # In single entry mode, set current time as start time and calculate end time
            current_time = self.now
            end_time = current_time + datetime.timedelta(minutes=30)
            self.start_time_edit.setTime(
                datetime.datetime.strptime(current_time.strftime("%H:%M"), "%H:%M").time()
            )
            self.end_time_edit.setTime(
                datetime.datetime.strptime(end_time.strftime("%H:%M"), "%H:%M").time()
            )
        
        form_layout.addRow("Start time:", self.start_time_edit)
        form_layout.addRow("End time:", self.end_time_edit)
        
        main_layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Entry")
        self.create_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.create_button)
        main_layout.addLayout(button_layout)
    
    @Slot(str)
    def on_project_changed(self, project_name):
        """Handle project selection change."""
        if project_name == 'Other':
            self.custom_project_label.setHidden(False)
            self.custom_project_edit.setHidden(False)
        else:
            self.custom_project_label.setHidden(True)
            self.custom_project_edit.setHidden(True)
    
    def accept(self):
        """Process form submission."""
        # Validate inputs
        if self.project_combo.currentText() == 'Other':
            custom_name = self.custom_project_edit.text().strip()
            if not custom_name:
                QMessageBox.critical(self, "Error", "Please enter a custom project name")
                return
            self.project_name = custom_name
        else:
            self.project_name = self.project_combo.currentText()
        
        # Get times
        start_time_value = self.start_time_edit.time()
        end_time_value = self.end_time_edit.time()
        
        # Ensure end time is after start time
        if start_time_value >= end_time_value:
            QMessageBox.critical(self, "Error", "End time must be after start time")
            return
        
        # Set the start and end times
        self.start_time = self.now.replace(
            hour=start_time_value.hour(),
            minute=start_time_value.minute()
        )
        
        self.end_time = self.now.replace(
            hour=end_time_value.hour(),
            minute=end_time_value.minute()
        )
        
        super().accept()

class SchedulerWindow(QMainWindow):
    # Define a signal to communicate from scheduler thread to main thread
    show_entry_signal = Signal()
    
    def __init__(self, projects):
        super().__init__()
        self.projects = projects
        
        self.setup_ui()
        
        # Connect the signal to the slot
        self.show_entry_signal.connect(self.show_entry_dialog)
        
        # Start scheduler after signal connections are set up
        self.setup_scheduler()
        
        # Timer to update current time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
    
    def setup_ui(self):
        """Set up the user interface for the scheduler window."""
        self.setWindowTitle("Time Tracking Scheduler")
        self.setMinimumSize(500, 200)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Time Tracking Scheduler")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Info
        info_label = QLabel("The scheduler is running for business days (Monday-Friday)")
        layout.addWidget(info_label)
        
        schedule_label = QLabel("Prompts will appear at 30-minute intervals from 9:30 AM to 5:30 PM")
        layout.addWidget(schedule_label)
        
        # CSV file location
        file_path = os.path.abspath(CSV_FILE)
        file_label = QLabel(f"CSV file location: {file_path}")
        font = file_label.font()
        font.setPointSize(8)
        file_label.setFont(font)
        layout.addWidget(file_label)
        
        # Current time
        self.status_label = QLabel("Current time: 00:00:00")
        layout.addWidget(self.status_label)
        
        # Current next scheduled time
        self.next_job_label = QLabel("Next prompt: Not scheduled")
        layout.addWidget(self.next_job_label)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Test button (aligned left)
        self.test_button = QPushButton("Test Dialog")
        self.test_button.clicked.connect(lambda: self.show_entry_signal.emit())
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()  # Pushes rest to the right
        
                # Stop button (aligned right)
        self.stop_button = QPushButton("Stop Scheduler")
        self.stop_button.clicked.connect(self.close)
        button_layout.addWidget(self.stop_button)
        
        # Make buttons the same size
        self.test_button.setMinimumWidth(100)
        self.stop_button.setMinimumWidth(100)
        
        layout.addLayout(button_layout)
    
    def setup_scheduler(self):
        """Set up the scheduler to run at specific times."""
        times = [
            "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
            "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", 
            "16:00", "16:30", "17:00", "17:30"
        ]
        
        for time_str in times:
            schedule.every().day.at(time_str).do(self.create_entry_if_business_day)
        
        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def run_scheduler(self):
        """Run the scheduler in a loop."""
        while True:
            schedule.run_pending()
            # Update the next job info
            next_job = schedule.next_run()
            if next_job:
                next_time = next_job.strftime("%H:%M:%S")
                # Need to use a signal-safe method to update UI from thread
                QMetaObject.invokeMethod(
                    self.next_job_label, 
                    "setText", 
                    Qt.QueuedConnection,  # Safe for cross-thread calls
                    Q_ARG(str, f"Next prompt: {next_time}")
                )
            time.sleep(1)
    
    def create_entry_if_business_day(self):
        """Create a time entry if today is a business day."""
        if is_business_day():
            # Emit the signal to show dialog from the main thread
            self.show_entry_signal.emit()
        else:
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][datetime.datetime.now().weekday()]
            print(f"Today is {day_name}. No timetracking entries on weekends.")
    
    @Slot()  # Mark as a slot that can be connected to signals
    def show_entry_dialog(self):
        """Show the time entry dialog. This is called on the main thread via the signal."""
        dialog = TimeEntryDialog(self.projects, use_scheduler=True, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.create_csv_entry(dialog.project_name, dialog.start_time, dialog.end_time)
    
    def create_csv_entry(self, project_name, start_time, end_time):
        """Create an entry in the CSV file."""
        # Format data for CSV - using MM/DD/YYYY format
        start_date = start_time.strftime("%m/%d/%Y")
        start_time_str = start_time.strftime("%H:%M")
        end_date = end_time.strftime("%m/%d/%Y")
        end_time_str = end_time.strftime("%H:%M")
        subject = f"Timetracking: {project_name}"
        
        # Create entry in CSV file - always append to end of file
        with open(CSV_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writerow({
                'Subject': subject,
                'Start Date': start_date,
                'Start Time': start_time_str,
                'End Date': end_date,
                'End Time': end_time_str,
                'Description': f"Time tracking for {project_name}"
            })
        
        QMessageBox.information(self, "Success", f"Entry added: {subject} on {start_date} at {start_time_str}")
    
    def update_time(self):
        """Update the current time display."""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(f"Current time: {current_time}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # No need to explicitly stop the scheduler thread as it's a daemon thread
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load projects
        self.projects = load_projects()
        
        # Check if projects need to be set up
        if not self.projects:
            self.setup_initial_projects()
        
        # Set up the user interface
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface for the main window."""
        self.setWindowTitle("Time Tracking CSV Generator")
        self.setMinimumSize(400, 300)
        
        # Create menu bar
        menubar = QMenuBar()
        self.setMenuBar(menubar)
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        edit_projects_action = QAction("Edit Projects", self)
        edit_projects_action.triggered.connect(self.edit_projects)
        file_menu.addAction(edit_projects_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        instructions_action = QAction("Import Instructions", self)
        instructions_action.triggered.connect(self.show_instructions)
        help_menu.addAction(instructions_action)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Time Tracking CSV Generator")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Add spacing
        layout.addSpacing(20)
        
        # Create buttons
        button_width = 200
        
        # Single entry button
        create_button = QPushButton("Create Single Entry")
        create_button.setMinimumWidth(button_width)
        create_button.clicked.connect(self.create_single_entry)
        layout.addWidget(create_button, alignment=Qt.AlignCenter)
        
        # Scheduler button
        scheduler_button = QPushButton("Start Scheduler")
        scheduler_button.setMinimumWidth(button_width)
        scheduler_button.clicked.connect(self.start_scheduler)
        layout.addWidget(scheduler_button, alignment=Qt.AlignCenter)
        
        # Project management button (new)
        projects_button = QPushButton("Manage Projects")
        projects_button.setMinimumWidth(button_width)
        projects_button.clicked.connect(self.edit_projects)
        layout.addWidget(projects_button, alignment=Qt.AlignCenter)
        
        # Instructions button
        instructions_button = QPushButton("Show Import Instructions")
        instructions_button.setMinimumWidth(button_width)
        instructions_button.clicked.connect(self.show_instructions)
        layout.addWidget(instructions_button, alignment=Qt.AlignCenter)
        
        # Exit button
        exit_button = QPushButton("Exit")
        exit_button.setMinimumWidth(button_width)
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button, alignment=Qt.AlignCenter)
        
        # Add spacing
        layout.addSpacing(20)
        
        # CSV file info
        file_path = os.path.abspath(CSV_FILE)
        file_label = QLabel(f"CSV file: {file_path}")
        font = file_label.font()
        font.setPointSize(8)
        file_label.setFont(font)
        file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(file_label)
        
        # Projects file info
        projects_path = os.path.abspath(PROJECTS_FILE)
        projects_label = QLabel(f"Projects file: {projects_path}")
        projects_label.setFont(font)
        projects_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(projects_label)

    
    def setup_initial_projects(self):
        """Set up initial projects if none exist."""
        # Show message explaining the importance of setting up projects
        QMessageBox.information(
            self,
            "Project Setup Required",
            "You need to set up your project list before using the application.\n\n"
            "If you cancel without configuring any projects, the program will exit."
        )
        
        dialog = ProjectsDialog([], self)
        if dialog.exec() == QDialog.Accepted and dialog.projects:
            self.projects = dialog.projects
            save_projects(self.projects)
        else:
            # If user cancels or doesn't configure any projects, exit the program
            QMessageBox.warning(
                self,
                "Setup Cancelled",
                "Project setup was cancelled or no projects were configured.\n"
                "The application will now exit."
            )
            # Close the main window, which will terminate the application
            self.close()
            # Use a timer to ensure the message box is closed before exiting
            QTimer.singleShot(100, lambda: QApplication.instance().quit())
    
    def edit_projects(self):
        """Edit project list."""
        dialog = ProjectsDialog(self.projects, self)
        if dialog.exec() == QDialog.Accepted:
            self.projects = dialog.projects
            save_projects(self.projects)
    
    def create_single_entry(self):
        """Show dialog to create a single time tracking entry."""
        # Check if today is a business day
        today = datetime.datetime.now().weekday()
        if today >= 5:  # Saturday or Sunday
            QMessageBox.information(
                self, 
                "Weekend", 
                f"Today is {'Saturday' if today == 5 else 'Sunday'}. Skipping timetracking."
            )
            return
        
        dialog = TimeEntryDialog(self.projects, use_scheduler=False, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.create_csv_entry(dialog.project_name, dialog.start_time, dialog.end_time)
    
    def create_csv_entry(self, project_name, start_time, end_time):
        """Create an entry in the CSV file."""
        # Format data for CSV - using MM/DD/YYYY format
        start_date = start_time.strftime("%m/%d/%Y")
        start_time_str = start_time.strftime("%H:%M")
        end_date = end_time.strftime("%m/%d/%Y")
        end_time_str = end_time.strftime("%H:%M")
        subject = f"Timetracking: {project_name}"
        
        # Create entry in CSV file - always append to end of file
        with open(CSV_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writerow({
                'Subject': subject,
                'Start Date': start_date,
                'Start Time': start_time_str,
                'End Date': end_date,
                'End Time': end_time_str,
                'Description': f"Time tracking for {project_name}"
            })
        
        QMessageBox.information(self, "Success", f"Entry added: {subject} on {start_date} at {start_time_str}")
    
    def start_scheduler(self):
        """Start the scheduler window."""
        self.scheduler_window = SchedulerWindow(self.projects)
        self.scheduler_window.show()
    
    def show_instructions(self):
        """Show instructions for importing the CSV file into Google Calendar."""
        msg = "How to import the CSV file into Google Calendar:\n\n"
        msg += "1. Go to calendar.google.com\n"
        msg += "2. Click on the gear icon (Settings) in the top-right corner\n"
        msg += "3. Select 'Settings'\n"
        msg += "4. In the left sidebar, click 'Import & export'\n"
        msg += "5. Click 'Select file from your computer' and select your CSV file\n"
        msg += "6. Choose the calendar to import events to\n"
        msg += "7. Click 'Import'\n\n"
        msg += f"Your CSV file is located at:\n{os.path.abspath(CSV_FILE)}"
        
        # Create message box with scrollable text area
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Import Instructions")
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Adjust the size of the message box
        text_width = QFontMetrics(msg_box.font()).horizontalAdvance('x') * 60  # 60 chars wide
        msg_box.setMinimumWidth(text_width)
        
        msg_box.exec()


def show_splash_message(message, duration=2000):
    """Show a splash message briefly and then hide it."""
    app = QApplication.instance()
    
    # Create a simple splash window
    splash = QWidget(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    splash.setAttribute(Qt.WA_TranslucentBackground)
    
    # Layout
    layout = QVBoxLayout(splash)
    
    # Message label with background
    frame = QFrame()
    frame.setFrameShape(QFrame.Panel)
    frame.setFrameShadow(QFrame.Raised)
    frame_layout = QVBoxLayout(frame)
    
    label = QLabel(message)
    label.setAlignment(Qt.AlignCenter)
    font = label.font()
    font.setPointSize(12)
    label.setFont(font)
    label.setMargin(20)
    
    frame_layout.addWidget(label)
    layout.addWidget(frame)
    
    # Center on screen
    splash.setGeometry(
        QApplication.desktop().screen().rect().center().x() - 200,
        QApplication.desktop().screen().rect().center().y() - 50,
        400, 100
    )
    
    splash.show()
    
    # Close after duration
    QTimer.singleShot(duration, splash.close)
    
    # Process events to show the splash
    app.processEvents()

def main():
    # Make sure the application can use high-DPI displays correctly
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))  # Use Fusion style for consistent cross-platform look
    
    # Initialize CSV file
    is_new = initialize_csv_file()
    if is_new:
        show_splash_message("Created new timetracking CSV file")
    
    # Show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
