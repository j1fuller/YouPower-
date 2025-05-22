# Author: SupportDone.com

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QDateEdit, QMessageBox, QDesktopWidget, QProgressBar, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import QDate, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QIcon
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from selenium.webdriver.common.keys import Keys

class AutomationWorker(QThread):
    """Worker thread to run Selenium automation."""
    progress = pyqtSignal(int)
    step_counter = 0
    finished = pyqtSignal(bool, str)
    driver = None

    def __init__(self, url, username, password, start_date, end_date, download_path):
        super().__init__()
        self.url = url
        self.username = username
        self.password = password
        self.start_date = start_date
        self.end_date = end_date
        self.download_path = download_path

    def login_to_portal(self, driver, url, username, password):
        """Perform login actions."""
        for attempt in range(3):
            driver.get(url)
            time.sleep(2)
            driver.refresh()

            try:
                print(f"Attempt {attempt + 1}: Logging in...")
                login_form_present = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "usernamex"))
                )

                if login_form_present:
                    username_field = driver.find_element(By.ID, "usernamex")
                    username_field.clear()
                    username_field.send_keys(username)
                    time.sleep(1)

                    password_field = driver.find_element(By.ID, "passwordx")
                    password_field.clear()
                    password_field.send_keys(password)
                    time.sleep(2)

                    driver.find_element(By.ID, "btnlogin").click()
                    time.sleep(3)
                else:
                    print("Login form not found. Assuming login was successful.")
                    return

                form_still_present = driver.find_elements(By.ID, "usernamex")
                if not form_still_present:
                    print("Login successful!")
                    return

            except Exception as e:
                print(f"Login attempt {attempt + 1} failed: {e}")

    @staticmethod
    def validate_and_format_date(date_string):
        """Validate and format the date to MMM DD, YYYY."""
        accepted_formats = ["%B %d, %Y", "%Y-%m-%d", "%d %B, %Y"]
        for date_format in accepted_formats:
            try:
                date_obj = datetime.strptime(date_string, date_format)
                return date_obj.strftime("%B %d, %Y")
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {date_string}. Expected formats: {', '.join(accepted_formats)}.")

    def download_file(self, driver, start_date, end_date, total_steps):
        """Download file with custom date range."""
        time.sleep(2)
        driver.get("https://myenergycenter.com/portal/Usage/Index")
        time.sleep(2)
        self.step_counter += 1
        self.progress.emit(int((self.step_counter / total_steps) * 100))

        start_date = self.validate_and_format_date(start_date)
        end_date = self.validate_and_format_date(end_date)

        green_button_download = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "gbloadpopup"))
        )
        green_button_download.click()
        print("Modal opened.")
        time.sleep(4)

        from_date_picker = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "gbfromdatepicker"))
        )
        driver.execute_script("arguments[0].removeAttribute('readonly')", from_date_picker)
        from_date_picker.clear()
        from_date_picker.send_keys(start_date)
        print(f"Start date entered: {start_date}")
        time.sleep(2)
        from_date_picker.send_keys(Keys.RETURN)

        to_date_picker = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "gbtodatepicker"))
        )
        driver.execute_script("arguments[0].removeAttribute('readonly')", to_date_picker)
        to_date_picker.clear()
        to_date_picker.send_keys(end_date)
        print(f"End date entered: {end_date}")
        time.sleep(2)
        to_date_picker.send_keys(Keys.RETURN)

        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btngbDataDownload"))
        )
        time.sleep(2)
        download_button.click()
        print("Download initiated.")
        time.sleep(5)
        self.step_counter += 1
        self.progress.emit(int((self.step_counter / total_steps) * 100))
        driver.get("https://myenergycenter.com/portal/Dashboard/index")
        time.sleep(2)

    def interact_with_dropdown(self, driver, start_date, end_date):
        """Interact with dropdown and handle progress."""
        dropdown_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-id='accountList']"))
        )
        dropdown_button.click()
        time.sleep(2)

        dropdown_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.dropdown-menu > li"))
        )
        total_items = len(dropdown_items)
        steps_per_cycle = 3
        total_steps = total_items * steps_per_cycle
        print(f"Found {total_items} items in the dropdown. Total steps: {total_steps}.")

        dropdown_button.click()
        time.sleep(2)

        for index in range(total_items):
            dropdown_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-id='accountList']"))
            )
            dropdown_button.click()
            time.sleep(2)

            clickable_item = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.dropdown-menu > li"))
            )[index]

            print(f"Selecting item {index + 1}: {clickable_item.text}")
            driver.execute_script("arguments[0].scrollIntoView(true);", clickable_item)
            clickable_item.click()
            self.step_counter += 1
            self.progress.emit(int((self.step_counter / total_steps) * 100))

            print("Waiting for page to reload...")
            try:
                WebDriverWait(driver, 20).until(EC.staleness_of(dropdown_button))
                print("Page reloaded successfully.")

                self.download_file(driver, start_date, end_date, total_steps)
            except Exception as e:
                print(f"Error waiting for page reload: {e}")
                raise
    def configure_driver(self):
        """Configure Chrome WebDriver with custom download folder."""
        
        normalized_path = self.download_path.replace("/", "\\")
        options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": normalized_path,  # Set custom download folder
            "download.prompt_for_download": False,  # Disable prompt
            "directory_upgrade": True,
        }
        options.add_experimental_option("prefs", prefs)
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def run(self):
        """Run the Selenium script."""
        try:
            self.driver = self.configure_driver()  # Use configured driver
            self.login_to_portal(self.driver, self.url, self.username, self.password)
            self.interact_with_dropdown(self.driver, self.start_date, self.end_date)
            self.finished.emit(True, "Automation completed successfully!")
        except Exception as e:
            self.finished.emit(False, f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()

class AutomationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouPower Billing Automation")
        self.setGeometry(100, 100, 500, 400)
        self.setWindowIcon(QIcon("icon.png"))

        self.worker = None

        self.center_window()

        self.image_label = QLabel()
        self.image_label.setPixmap(QPixmap("logo.png"))
        self.image_label.setAlignment(Qt.AlignCenter)

        self.url_label = QLabel("https://myenergycenter.com/portal/PreLogin/Validate")
        self.url_input = QLineEdit()

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.start_date_label = QLabel("Start Date:")
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setDisplayFormat("dd MMMM, yyyy")

        self.end_date_label = QLabel("End Date:")
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setDisplayFormat("dd MMMM, yyyy")

        self.download_label = QLabel("Download Folder:")

        # Create a horizontal layout for download input and browse button
        self.download_layout = QHBoxLayout()
        self.download_input = QLineEdit()
        self.download_input.setReadOnly(True)  # Make input field read-only
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)

        self.download_layout.addWidget(self.download_input)
        self.download_layout.addWidget(self.browse_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.start_button = QPushButton("Start Automation")
        self.start_button.clicked.connect(self.start_automation)

        self.stop_button = QPushButton("Stop Automation")
        self.stop_button.clicked.connect(self.stop_automation)
        self.stop_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.url_label)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.start_date_label)
        layout.addWidget(self.start_date_input)
        layout.addWidget(self.end_date_label)
        layout.addWidget(self.end_date_input)
        layout.addWidget(self.download_label)
        layout.addLayout(self.download_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def browse_folder(self):
        """Open a folder dialog to select the download folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_input.setText(folder)
            
    def center_window(self):
        """Position the application window towards the right side of the screen with a top margin."""
        screen_geometry = QDesktopWidget().availableGeometry()
        frame_geometry = self.frameGeometry()
        right_margin = 50
        top_margin = 70
        x_position = screen_geometry.right() - frame_geometry.width() - right_margin
        y_position = screen_geometry.top() + top_margin
        self.move(x_position, y_position)

    def start_automation(self):
        """Start the Selenium automation process."""
        url = "https://myenergycenter.com/portal/PreLogin/Validate"
        username = self.username_input.text()
        password = self.password_input.text()
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        download_path = self.download_input.text()

        if not url or not username or not password or not download_path:
            QMessageBox.warning(self, "Input Error", "Please fill all fields and select a download folder!")
            return

        self.set_form_enabled(False)
        self.worker = AutomationWorker(url, username, password, start_date, end_date, download_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_automation_finished)
        self.worker.start()

    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def on_automation_finished(self, success, message):
        """Handle completion of the automation process."""
        self.set_form_enabled(True)
        self.progress_bar.setValue(100 if success else 0)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def stop_automation(self):
        """Stop the Selenium automation process and close the application."""
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Stopping", "Stopping the automation process...")
            self.worker.terminate()
            self.worker.exit()
            self.worker.quit()
            self.worker = None

        QApplication.instance().quit()

    def set_form_enabled(self, enabled):
        """Enable/disable form and buttons."""
        self.url_input.setEnabled(enabled)
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.start_date_input.setEnabled(enabled)
        self.end_date_input.setEnabled(enabled)
        self.download_input.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutomationApp()
    window.show()
    sys.exit(app.exec())