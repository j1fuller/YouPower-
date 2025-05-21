# youpower_pge.py - Simple PG&E Green Button Data Scraper
import sys
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, 
    QDateEdit, QMessageBox, QDesktopWidget, QProgressBar, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import QDate, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QIcon
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys

class PGEScraper(QThread):
    """Worker thread to run Selenium automation for PG&E."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    driver = None

    def __init__(self, username, password, start_date, end_date, download_path):
        super().__init__()
        self.username = username
        self.password = password
        self.start_date = start_date
        self.end_date = end_date
        self.download_path = download_path
        self.step = 0
        self.total_steps = 5

    def update_progress(self, step_completed=True):
        """Update progress bar."""
        if step_completed:
            self.step += 1
        self.progress.emit(int((self.step / self.total_steps) * 100))

    def login_to_pge(self, driver):
        """Perform login to PG&E portal."""
        try:
            print("Logging in to PG&E...")
            driver.get("https://www.pge.com/en/login")
            time.sleep(3)
            
            # Find and fill username field
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(1)
            
            # Find and fill password field
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            # Click login button
            login_button = driver.find_element(By.ID, "login")
            login_button.click()
            time.sleep(5)
            
            # Verify login was successful
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Energy Usage')]"))
                )
                print("Login successful!")
                self.update_progress()
                return True
            except:
                print("Login failed: couldn't find Energy Usage link")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def download_green_button_data(self, driver):
        """Navigate to Green Button and download data."""
        try:
            # Click on Energy Usage
            energy_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Energy Usage')]"))
            )
            energy_link.click()
            time.sleep(5)
            self.update_progress()
            
            # Click on Energy Usage Details 
            details_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Energy Usage Details')]"))
            )
            details_link.click()
            time.sleep(5)
            self.update_progress()
            
            # Scroll down to find Green Button
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find and click Green Button
            green_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Green Button') or contains(@class, 'green-button')]"))
            )
            green_button.click()
            time.sleep(3)
            self.update_progress()
            
            # Select date range option
            range_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='radio' and @value='range']"))
            )
            range_option.click()
            time.sleep(2)
            
            # Format dates
            from_date = self.start_date.toString("MMMM d, yyyy")
            to_date = self.end_date.toString("MMMM d, yyyy")
            
            # Fill in date fields
            from_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "from-date"))
            )
            from_field.clear()
            from_field.send_keys(from_date)
            time.sleep(1)
            
            to_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "to-date"))
            )
            to_field.clear()
            to_field.send_keys(to_date)
            time.sleep(1)
            
            # Click download button
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download')]"))
            )
            download_button.click()
            print("Download initiated")
            time.sleep(10)  # Wait for download to complete
            self.update_progress()
            
            return True
            
        except Exception as e:
            print(f"Error downloading data: {e}")
            return False
    
    def configure_driver(self):
        """Configure Chrome WebDriver with custom download folder."""
        normalized_path = self.download_path.replace("/", "\\")
        options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": normalized_path,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
        }
        options.add_experimental_option("prefs", prefs)
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def run(self):
        """Run the Selenium script."""
        try:
            self.driver = self.configure_driver()
            
            if not self.login_to_pge(self.driver):
                self.finished.emit(False, "Login failed. Please check your credentials.")
                return
                
            if not self.download_green_button_data(self.driver):
                self.finished.emit(False, "Failed to download Green Button data.")
                return
                
            self.finished.emit(True, "Successfully downloaded PG&E Green Button data!")
            
        except Exception as e:
            self.finished.emit(False, f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()


class PGEScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouPower PG&E Data Scraper")
        self.setGeometry(100, 100, 450, 400)
        self.setWindowIcon(QIcon("icon.ico") if os.path.exists("icon.ico") else None)

        self.worker = None
        self.center_window()
        self.init_ui()
        
    def center_window(self):
        """Center the window on the screen."""
        frame = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())
        
    def init_ui(self):
        """Initialize the user interface."""
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Logo
        self.logo_label = QLabel()
        if os.path.exists("logo.png"):
            self.logo_label.setPixmap(QPixmap("logo.png").scaledToWidth(200))
            self.logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.logo_label)
        
        # Username input
        self.username_label = QLabel("PG&E Username:")
        layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)
        
        # Password input
        self.password_label = QLabel("PG&E Password:")
        layout.addWidget(self.password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # Date range
        self.start_date_label = QLabel("Start Date:")
        layout.addWidget(self.start_date_label)
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate().addMonths(-1))
        layout.addWidget(self.start_date_input)
        
        self.end_date_label = QLabel("End Date:")
        layout.addWidget(self.end_date_label)
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        layout.addWidget(self.end_date_input)
        
        # Download folder
        self.download_label = QLabel("Download Folder:")
        layout.addWidget(self.download_label)
        
        download_layout = QHBoxLayout()
        self.download_input = QLineEdit()
        self.download_input.setReadOnly(True)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        download_layout.addWidget(self.download_input)
        download_layout.addWidget(self.browse_button)
        layout.addLayout(download_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    def browse_folder(self):
        """Open a dialog to select download folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_input.setText(folder)
            
    def start_scraping(self):
        """Start the scraping process."""
        # Validate inputs
        username = self.username_input.text()
        password = self.password_input.text()
        start_date = self.start_date_input.date()
        end_date = self.end_date_input.date()
        download_path = self.download_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter your PG&E username and password.")
            return
            
        if not download_path:
            QMessageBox.warning(self, "Input Error", "Please select a download folder.")
            return
            
        # Disable UI elements during scraping
        self.set_enabled(False)
        
        # Create and start worker thread
        self.worker = PGEScraper(username, password, start_date, end_date, download_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def update_progress(self, value):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
        
    def on_finished(self, success, message):
        """Handle completion of scraping."""
        self.set_enabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
            
    def set_enabled(self, enabled):
        """Enable or disable UI elements."""
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.start_date_input.setEnabled(enabled)
        self.end_date_input.setEnabled(enabled)
        self.download_input.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PGEScraperApp()
    window.show()
    sys.exit(app.exec_())
