import csv
import os
import time
import random
import pickle
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from tqdm import tqdm
from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)

# Install ChromeDriver if needed
chromedriver_autoinstaller.install()

# Folders and Files
COOKIES_FOLDER = 'cookies'
DATA_FILE = 'data.txt'
MESSAGE_FILE = 'message.txt'
COMMENT_FILE = 'comment.txt'
CSV_LOG_FILE = 'dm_log.csv'
CSV_INTERACTION_LOG = 'interaction_log.csv'

# Global variable declaration
global default_delay_range
default_delay_range = (10, 40)  # Default delay range in seconds

# Fungsi untuk menyaring karakter non-BMP (misalnya emoji di luar Basic Multilingual Plane)
def remove_non_bmp(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF)

# Function to read usernames from a file
def read_usernames(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + f"File {file_path} not found.")
        return []

# Function to read usernames and messages from a file (untuk DM)
def read_usernames_and_messages(data_file, message_file):
    try:
        with open(data_file, 'r', encoding='utf-8') as data:
            usernames = [line.strip() for line in data if line.strip()]
        
        with open(message_file, 'r', encoding='utf-8') as msg:
            messages = [line.strip() for line in msg if line.strip()]
        
        if len(messages) < len(usernames):
            messages = messages * (len(usernames) // len(messages) + 1)
        
        return list(zip(usernames, messages[:len(usernames)]))
    
    except FileNotFoundError as e:
        print(Fore.RED + f"File not found: {e}")
        return []

# Fungsi untuk membaca daftar komentar dari file comment.txt
def read_comments(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + f"File {file_path} not found.")
        return []

# Function to log DM results to a CSV file (dengan Timestamp)
def log_dm_result(csv_file, username, status):
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['Username', 'Status', 'Timestamp'])
        writer.writerow([username, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

# FUNCTION: Log follow result ke file CSV
def log_follow_result(csv_file, username, status):
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['Username', 'Follow_Status', 'Timestamp'])
        writer.writerow([username, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

# Function to format message with username
def format_message(message, username):
    # Bersihkan username: hapus whitespace, newline, dan hapus "@" di awal jika ada
    username_clean = username.strip().lstrip("@").replace("\r", "").replace("\n", "")
    return message.replace("{username}", f"@{username_clean}")

# Function to load cookies with increased wait time
def load_cookies(driver, account_name):
    cookies_file = os.path.join(COOKIES_FOLDER, f"twitter_{account_name}.pkl")
    if os.path.exists(cookies_file):
        with open(cookies_file, 'rb') as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print(Fore.GREEN + f"Cookies loaded for Twitter account {account_name}.")
        time.sleep(5)
    else:
        print(Fore.YELLOW + f"Cookies not found for Twitter account {account_name}. Manual login required.")

# Function to save cookies
def save_cookies(driver, account_name):
    cookies = driver.get_cookies()
    cookies_file = os.path.join(COOKIES_FOLDER, f"twitter_{account_name}.pkl")
    with open(cookies_file, 'wb') as file:
        pickle.dump(cookies, file)
    print(Fore.GREEN + f"Cookies saved for Twitter account {account_name}.")

# Initialize Chrome Driver with options
def init_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    return webdriver.Chrome(options=chrome_options)

# Function to update delay range
def update_delay_settings():
    global default_delay_range
    try:
        print(Fore.CYAN + "\nCurrent delay range:", default_delay_range)
        min_delay = int(input(Fore.LIGHTYELLOW_EX + "Enter minimum delay (in seconds): "))
        max_delay = int(input(Fore.LIGHTYELLOW_EX + "Enter maximum delay (in seconds): "))
        
        if min_delay > 0 and max_delay > min_delay:
            default_delay_range = (min_delay, max_delay)
            print(Fore.GREEN + f"Delay range updated to: {default_delay_range} seconds")
        else:
            print(Fore.RED + "Invalid input. Max delay must be greater than min delay and both must be positive.")
    except ValueError:
        print(Fore.RED + "Invalid input. Please enter numbers only.")

# =============================================================
# FUNCTION: Send DM (Auto DM)
# =============================================================
def send_dm(driver, username, message, debug=False):
    try:
        formatted_message = format_message(message, username)
        driver.get(f"https://twitter.com/{username}")
        time.sleep(3)

        try:
            xpath_options = [
                "//div[@data-testid='sendDMFromProfile']",
                "//button[@data-testid='sendDMFromProfile']",
                "//div[@role='button' and @aria-label='Message']",
            ]
            message_button = None
            for xpath in xpath_options:
                try:
                    message_button = driver.find_element(By.XPATH, xpath)
                    if message_button.is_displayed():
                        break
                except:
                    continue

            if not message_button:
                print(Fore.YELLOW + f"'Message' button not found for {username}.")
                return "Failed to send DM"

            driver.execute_script("arguments[0].scrollIntoView(true);", message_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", message_button)
        except Exception as e:
            print(Fore.RED + f"'Message' button not found for {username}: {e}")
            return "Failed to send DM"

        try:
            message_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-offset-key and contains(@class, 'public-DraftStyleDefault-block')]"))
            )
            message_input.click()
            message_input.send_keys(formatted_message)
            time.sleep(1)
            message_input.send_keys(Keys.ENTER)
        except Exception as e:
            print(Fore.RED + f"Message input area not found: {e}")
            return "Failed to send DM"

        print(Fore.GREEN + f"DM sent to {username}")
        return "Sent"
    except Exception as e:
        if debug:
            print(Fore.RED + f"Error sending DM to {username}: {e}")
        return "Error"        

# =============================================================
# FUNCTION: Like Latest Tweet menggunakan atribut data-testid
# =============================================================
def like_latest_tweet(driver, username, debug=False):
    try:
        driver.get(f"https://twitter.com/{username}")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        like_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@data-testid='like']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", like_button)
        time.sleep(2)
        print(Fore.GREEN + f"Liked latest tweet from {username}")
        return "Liked"
    except Exception as e:
        if debug:
            print(Fore.RED + f"Error liking tweet: {str(e)}")
        return "Error"

# =============================================================
# FUNCTION: Comment on Latest Tweet menggunakan atribut data-testid
# =============================================================
def comment_latest_tweet(driver, username, comment, debug=False):
    try:
        formatted_comment = remove_non_bmp(format_message(comment, username))
        driver.get(f"https://twitter.com/{username}")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@data-testid='reply']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", reply_button)
        time.sleep(2)
        
        comment_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']"))
        )
        comment_input.click()
        comment_input.send_keys(formatted_comment)
        time.sleep(1)
        
        tweet_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tweetButton']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", tweet_button)
        time.sleep(2)
        
        print(Fore.GREEN + f"Commented on {username}'s latest tweet")
        return "Commented"
    except Exception as e:
        if debug:
            print(Fore.RED + f"Error commenting: {str(e)}")
        return "Error"

# =============================================================
# FUNCTION: Follow a user using stable attribute based on element attributes
# =============================================================
def follow_user(driver, username, debug=False):
    try:
        driver.get(f"https://twitter.com/{username}")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        try:
            # Menggunakan XPath berdasarkan atribut aria-label dan data-testid
            follow_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Follow') and contains(@data-testid, '-follow')]"))
            )
        except Exception as inner_e:
            if debug:
                print(Fore.YELLOW + f"Follow button tidak ditemukan untuk {username}. Exception: {inner_e}")
            return "Already Followed"
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", follow_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", follow_button)
        time.sleep(2)
        print(Fore.GREEN + f"Followed {username}")
        return "Followed"
    except Exception as e:
        if debug:
            print(Fore.RED + f"Error following {username}: {str(e)}")
        return "Error"

# =============================================================
# FUNCTION: Start interaction process (like & comment)
# =============================================================
def start_interaction():
    account_name = input(Fore.LIGHTYELLOW_EX + "Enter Twitter account name: ").strip()
    driver = init_chrome_driver()

    driver.get("https://twitter.com/login")
    time.sleep(5)
    load_cookies(driver, account_name)

    if not any(cookie['name'] == 'auth_token' for cookie in driver.get_cookies()):
        print(Fore.LIGHTYELLOW_EX + "Manual login required.")
        input(Fore.LIGHTMAGENTA_EX + "Press Enter after logging in...")
        save_cookies(driver, account_name)

    usernames = read_usernames(DATA_FILE)
    comments = read_comments(COMMENT_FILE)

    if not usernames:
        print(Fore.LIGHTRED_EX + "Username list is empty. Script stopped.")
        driver.quit()
        return

    if not comments:
        print(Fore.LIGHTRED_EX + "Comment list is empty. Script stopped.")
        driver.quit()
        return

    if len(comments) < len(usernames):
        comments = comments * (len(usernames) // len(comments) + 1)

    print(Fore.CYAN + f"Starting interactions with delay range: {default_delay_range[0]}-{default_delay_range[1]} seconds")
    
    for username, comment in tqdm(zip(usernames, comments[:len(usernames)]), total=len(usernames), desc="Processing", unit="user"):
        like_status = like_latest_tweet(driver, username, debug=True)
        time.sleep(2)
        comment_status = comment_latest_tweet(driver, username, comment, debug=True)
        
        log_dm_result(CSV_INTERACTION_LOG, username, f"Like: {like_status}, Comment: {comment_status}")

        delay = random.randint(*default_delay_range)
        print(Fore.LIGHTMAGENTA_EX + f"Waiting for {delay} seconds before next interaction...")
        time.sleep(delay)

    print(Fore.GREEN + "\nInteraction process completed!")
    driver.quit()

# =============================================================
# FUNCTION: Start follow process
# =============================================================
def start_follow():
    account_name = input(Fore.LIGHTYELLOW_EX + "Enter Twitter account name: ").strip()
    driver = init_chrome_driver()

    driver.get("https://twitter.com/login")
    time.sleep(5)
    load_cookies(driver, account_name)

    if not any(cookie['name'] == 'auth_token' for cookie in driver.get_cookies()):
        print(Fore.LIGHTYELLOW_EX + "Manual login required.")
        input(Fore.LIGHTMAGENTA_EX + "Press Enter after logging in...")
        save_cookies(driver, account_name)

    usernames = read_usernames(DATA_FILE)
    if not usernames:
        print(Fore.LIGHTRED_EX + "Username list is empty. Script stopped.")
        driver.quit()
        return

    print(Fore.CYAN + "Starting follow process...")
    for username in tqdm(usernames, desc="Following", unit="user"):
        status = follow_user(driver, username, debug=True)
        print(f"Follow status for {username}: {status}")
        log_follow_result("follow_log.csv", username, status)
        delay = random.randint(*default_delay_range)
        print(Fore.LIGHTMAGENTA_EX + f"Waiting for {delay} seconds before next follow...")
        time.sleep(delay)

    print(Fore.GREEN + "Follow process completed!")
    driver.quit()

# =============================================================
# FUNCTION: Start Selenium with cookies (manual login)
# =============================================================
def start_selenium():
    account_name = input(Fore.LIGHTYELLOW_EX + "Enter Twitter account name: ").strip()
    driver = init_chrome_driver()
    
    driver.get("https://twitter.com/login")
    time.sleep(5)
    load_cookies(driver, account_name)
    
    if not any(cookie['name'] == 'auth_token' for cookie in driver.get_cookies()):
        print(Fore.LIGHTYELLOW_EX + "Manual login required.")
        input(Fore.LIGHTMAGENTA_EX + "Press Enter after logging in...")
        save_cookies(driver, account_name)

    print(Fore.GREEN + f"Selenium ready for Twitter account {account_name}.")
    driver.quit()

# =============================================================
# FUNCTION: Start Auto DM Twitter
# =============================================================
def start_auto_dm():
    global default_delay_range
    account_name = input(Fore.LIGHTYELLOW_EX + "Enter Twitter account name: ").strip()
    driver = init_chrome_driver()

    driver.get("https://twitter.com/login")
    time.sleep(5)
    load_cookies(driver, account_name)

    if not any(cookie['name'] == 'auth_token' for cookie in driver.get_cookies()):
        print(Fore.LIGHTYELLOW_EX + "Manual login required.")
        input(Fore.LIGHTMAGENTA_EX + "Press Enter after logging in...")
        save_cookies(driver, account_name)

    user_messages = read_usernames_and_messages(DATA_FILE, MESSAGE_FILE)

    if not user_messages:
        print(Fore.LIGHTRED_EX + "Username list or message list is empty. Script stopped.")
        driver.quit()
        return

    print(Fore.CYAN + f"Starting to send DMs with delay range: {default_delay_range[0]}-{default_delay_range[1]} seconds")
    
    for username, message in tqdm(user_messages, desc="Sending DMs", unit="user"):
        status = send_dm(driver, username, message, debug=False)
        log_dm_result(CSV_LOG_FILE, username, status)

        delay = random.randint(*default_delay_range)
        print(Fore.LIGHTMAGENTA_EX + f"Waiting for {delay} seconds before next DM...")
        time.sleep(delay)

    print(Fore.GREEN + "\nDM sending process completed!")
    driver.quit()

# =============================================================
# MAIN MENU
# =============================================================
def main_menu():
    print(Fore.MAGENTA + """
     ██╗███╗   ██╗███████╗ ██╗██████╗ ███████╗
     ██║████╗  ██║██╔════╝███║██╔══██╗██╔════╝
     ██║██╔██╗ ██║███████╗╚██║██║  ██║█████╗  
     ██║██║╚██╗██║╚════██║ ██║██║  ██║██╔══╝  
     ██║██║ ╚████║███████║ ██║██████╔╝███████╗
     ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═╝╚═════╝ ╚══════╝
           Twitter Auto DM Bot v1.6                      
═══════════════════════════════════════════════
""" + Style.RESET_ALL)

    while True:
        print(Fore.LIGHTMAGENTA_EX + "\nChoose an option:")
        print(Fore.LIGHTCYAN_EX + "1. Start Selenium (manual login and save cookies)")
        print(Fore.LIGHTCYAN_EX + "2. Update Delay Settings")
        print(Fore.LIGHTCYAN_EX + "3. Start Auto DM Twitter")
        print(Fore.LIGHTCYAN_EX + "4. Like & Comment Latest Tweets")
        print(Fore.LIGHTCYAN_EX + "5. Follow Users")
        print(Fore.LIGHTCYAN_EX + "6. Exit")
        choice = input(Fore.LIGHTYELLOW_EX + "Enter your choice (1/2/3/4/5/6): ")

        if choice == '1':
            start_selenium()
        elif choice == '2':
            update_delay_settings()
        elif choice == '3':
            start_auto_dm()
        elif choice == '4':
            start_interaction()
        elif choice == '5':
            start_follow()
        elif choice == '6':
            print(Fore.LIGHTRED_EX + "Exiting the program.")
            break
        else:
            print(Fore.LIGHTRED_EX + "Invalid choice. Please try again.")

if __name__ == "__main__":
    if not os.path.exists(COOKIES_FOLDER):
        os.makedirs(COOKIES_FOLDER)
    main_menu()
