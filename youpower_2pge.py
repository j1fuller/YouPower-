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
        """Perform login to PG&E mobile portal."""
        try:
            print("Logging in to PG&E...")
            driver.get("https://m.pge.com/?WT.mc_id=Vanity_myaccount#login")
            time.sleep(3)
            
            # Try different selectors for username and password fields
            # Mobile site might use different IDs or classes
            username_selectors = [
                (By.ID, "username"),
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.XPATH, "//input[@placeholder='Username' or contains(@placeholder, 'user')]")
            ]
            
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@placeholder='Password' or contains(@placeholder, 'pass')]")
            ]
            
            login_button_selectors = [
                (By.ID, "login"),
                (By.XPATH, "//button[contains(text(), 'Log In') or contains(text(), 'Sign In')]"),
                (By.CSS_SELECTOR, "button.login-button, input[type='submit']")
            ]
            
            # Find and fill username field
            username_field = None
            for selector_type, selector in username_selectors:
                try:
                    username_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    if username_field:
                        print(f"Found username field with selector: {selector}")
                        break
                except:
                    continue
            
            if not username_field:
                print("Could not find username field")
                return False
                
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(1)
            
            # Find and fill password field
            password_field = None
            for selector_type, selector in password_selectors:
                try:
                    password_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    if password_field:
                        print(f"Found password field with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_field:
                print("Could not find password field")
                return False
                
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            # Find and click login button
            login_button = None
            for selector_type, selector in login_button_selectors:
                try:
                    login_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    if login_button:
                        print(f"Found login button with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                print("Could not find login button")
                return False
                
            login_button.click()
            time.sleep(5)
            
            # Verify login was successful - looking for any indicators of successful login
            success_indicators = [
                "//a[contains(text(), 'Energy Usage')]",
                "//a[contains(text(), 'Account')]",
                "//a[contains(text(), 'Dashboard')]",
                "//div[contains(@class, 'dashboard')]"
            ]
            
            for indicator in success_indicators:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                    print(f"Login successful! Found indicator: {indicator}")
                    self.update_progress()
                    return True
                except:
                    continue
            
            print("Login verification failed - couldn't find success indicators")
            return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def download_green_button_data(self, driver):
        """Navigate to Green Button and download data."""
        try:
            # Try switching to desktop view for better navigation if we're on mobile
            try:
                # Look for a desktop version link or switch to desktop URL
                desktop_links = [
                    (By.XPATH, "//a[contains(text(), 'Desktop') or contains(text(), 'Full Site')]"),
                    (By.CSS_SELECTOR, "a.desktop-link")
                ]
                
                for selector_type, selector in desktop_links:
                    try:
                        desktop_link = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((selector_type, selector))
                        )
                        desktop_link.click()
                        print("Switched to desktop view")
                        time.sleep(5)
                        break
                    except:
                        continue
                        
                # If no desktop link found, manually navigate to desktop URL
                if "m.pge.com" in driver.current_url:
                    driver.get("https://www.pge.com/myaccount/dashboard")
                    time.sleep(5)
                    print("Navigated to desktop dashboard")
            except:
                print("Could not switch to desktop view, continuing with current view")
            
            # Multiple approaches to navigate to Energy Usage
            energy_usage_selectors = [
                (By.XPATH, "//a[contains(text(), 'Energy Usage')]"),
                (By.XPATH, "//a[contains(@href, 'energy-usage')]"),
                (By.XPATH, "//span[contains(text(), 'Energy Usage')]/parent::a"),
                (By.XPATH, "//div[contains(text(), 'Energy Usage')]")
            ]
            
            print("Attempting to navigate to Energy Usage...")
            for selector_type, selector in energy_usage_selectors:
                try:
                    energy_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    energy_link.click()
                    print(f"Clicked Energy Usage with selector: {selector}")
                    time.sleep(5)
                    self.update_progress()
                    break
                except:
                    continue
            
            # If we couldn't find Energy Usage link, try direct navigation
            if "usage" not in driver.current_url.lower():
                print("Direct navigation to Energy Usage page")
                driver.get("https://www.pge.com/myaccount/usage")
                time.sleep(5)
            
            # Try to find Energy Usage Details or similar link
            details_selectors = [
                (By.XPATH, "//a[contains(text(), 'Energy Usage Details')]"),
                (By.XPATH, "//a[contains(@href, 'usage-details')]"),
                (By.XPATH, "//a[contains(text(), 'Usage Details')]"),
                (By.XPATH, "//span[contains(text(), 'Details')]/parent::a")
            ]
            
            print("Looking for Energy Usage Details...")
            for selector_type, selector in details_selectors:
                try:
                    details_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    details_link.click()
                    print(f"Clicked Details with selector: {selector}")
                    time.sleep(5)
                    self.update_progress()
                    break
                except:
                    continue
            
            # If we couldn't find Details link, try direct navigation
            if "details" not in driver.current_url.lower():
                print("Direct navigation to Usage Details page")
                driver.get("https://www.pge.com/myaccount/usage/details")
                time.sleep(5)
            
            # Scroll down to find Green Button
            print("Scrolling to find Green Button...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Multiple selectors for Green Button
            green_button_selectors = [
                (By.XPATH, "//button[contains(text(), 'Green Button')]"),
                (By.XPATH, "//a[contains(text(), 'Green Button')]"),
                (By.CSS_SELECTOR, "button.green-button"),
                (By.XPATH, "//img[contains(@src, 'green-button')]/parent::*"),
                (By.XPATH, "//div[contains(text(), 'Green Button')]")
            ]
            
            green_button = None
            for selector_type, selector in green_button_selectors:
                try:
                    green_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    if green_button:
                        print(f"Found Green Button with selector: {selector}")
                        green_button.click()
                        time.sleep(3)
                        self.update_progress()
                        break
                except:
                    continue
            
            if not green_button:
                print("Could not find Green Button, trying to locate by screenshot...")
                # If the button isn't found, we might want to do something else or return False
                return False
            
            # Multiple selectors for date range option
            range_option_selectors = [
                (By.XPATH, "//input[@type='radio' and @value='range']"),
                (By.XPATH, "//input[@type='radio' and contains(@id, 'range')]"),
                (By.XPATH, "//label[contains(text(), 'range of days')]//input"),
                (By.XPATH, "//label[contains(text(), 'range')]//input")
            ]
            
            print("Selecting date range option...")
            for selector_type, selector in range_option_selectors:
                try:
                    range_option = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    range_option.click()
                    print(f"Selected date range with selector: {selector}")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Format dates
            from_date = self.start_date.toString("MMMM d, yyyy")
            to_date = self.end_date.toString("MMMM d, yyyy")
            
            # Multiple selectors for date fields
            from_field_selectors = [
                (By.ID, "from-date"),
                (By.XPATH, "//input[contains(@id, 'from')]"),
                (By.XPATH, "//input[contains(@name, 'from')]"),
                (By.XPATH, "//label[contains(text(), 'From')]/following-sibling::input"),
                (By.XPATH, "//label[contains(text(), 'From')]/parent::*/input")
            ]
            
            to_field_selectors = [
                (By.ID, "to-date"),
                (By.XPATH, "//input[contains(@id, 'to')]"),
                (By.XPATH, "//input[contains(@name, 'to')]"),
                (By.XPATH, "//label[contains(text(), 'To')]/following-sibling::input"),
                (By.XPATH, "//label[contains(text(), 'To')]/parent::*/input")
            ]
            
            # Find and fill From date field
            print("Entering date range...")
            from_field = None
            for selector_type, selector in from_field_selectors:
                try:
                    from_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    if from_field:
                        print(f"Found From date field with selector: {selector}")
                        break
                except:
                    continue
            
            if from_field:
                from_field.clear()
                from_field.send_keys(from_date)
                time.sleep(1)
            else:
                print("Could not find From date field")
            
            # Find and fill To date field
            to_field = None
            for selector_type, selector in to_field_selectors:
                try:
                    to_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    if to_field:
                        print(f"Found To date field with selector: {selector}")
                        break
                except:
                    continue
            
            if to_field:
                to_field.clear()
                to_field.send_keys(to_date)
                time.sleep(1)
            else:
                print("Could not find To date field")
            
            # Multiple selectors for download button
            download_button_selectors = [
                (By.XPATH, "//button[contains(text(), 'Download')]"),
                (By.XPATH, "//a[contains(text(), 'Download')]"),
                (By.CSS_SELECTOR, "button.download-button"),
                (By.XPATH, "//input[@type='submit' and contains(@value, 'Download')]")
            ]
            
            print("Initiating download...")
            for selector_type, selector in download_button_selectors:
                try:
                    download_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    download_button.click()
                    print(f"Clicked download button with selector: {selector}")
                    time.sleep(10)  # Wait for download to complete
                    self.update_progress()
                    return True
                except:
                    continue
            
            print("Could not find download button")
            return False
            
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
        
        # Add additional options for better compatibility
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Enable logging for debugging
        options.add_argument("--enable-logging")
        options.add_argument("--v=1")
        
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
