from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from datetime import datetime
import os
import sqlite3
import time
import re
import requests
import json

load_dotenv()

discord_email = os.getenv("DISCORD_EMAIL")
discord_password = os.getenv("DISCORD_PASSWORD")
profile_path = os.getenv("CHROME_PROFILE_PATH")
personality = os.getenv("PERSONALITY")

def init_memory_db():
    conn = sqlite3.connect('ai_memory.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_message TEXT,
            bot_response TEXT,
            timestamp REAL
        )
    ''')
    conn.commit()
    return conn

# Save memory to the database
def save_memory(conn, username, user_message, bot_response):
    c = conn.cursor()
    c.execute('INSERT INTO memory (username, user_message, bot_response, timestamp) VALUES (?, ?, ?, ?)',
              (username, user_message, bot_response, time.time()))
    conn.commit()

# Load memory from the database (limit by the most recent interactions)
def load_memory(conn, username, limit=5):
    c = conn.cursor()
    c.execute('SELECT user_message, bot_response FROM memory WHERE username = ? ORDER BY timestamp DESC LIMIT ?',
              (username, limit))
    return c.fetchall()

# Set up the Chrome browser with an existing profile
options = webdriver.ChromeOptions()

#profile path instead of login
options.add_argument(f"user-data-dir={profile_path}")

options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-infobars')
options.add_argument('--start-maximized')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

character_personality = personality

user_memory = {}

def discord_login(email, password):
    driver.get("https://discord.com/channels/@me")

    if False: #Shouldnt use because bannble
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(email)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()

    time.sleep(5)  # wait for discord to log in

def sanitize_message(message):
    return re.sub(r'[^\u0000-\uFFFF]', '', message)

def send_test_message(group_chat_name, message):
    group_chat = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, f"//div[text()='{group_chat_name}']"))
    )
    group_chat.click()

    message_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='markup_f8f345 editor_a552a6 slateTextArea_e52116 fontSize16Padding_d0696b']"))
    )
    driver.execute_script("arguments[0].click();", message_box)
    message_box.send_keys(message)
    message_box.send_keys("\n")

    print(f"Message sent to {group_chat_name}: {message}")

def get_username_and_message():
    try:

        message_element = driver.find_elements(By.CSS_SELECTOR, "div[class*='messageContent']")[-1]
        username_element = driver.find_elements(By.CSS_SELECTOR, "span[class*='username']")[-1]
        
        latest_message = message_element.text
        username = username_element.text
        return username, latest_message
    except Exception as e:
        print(f"Error while extracting username and message: {e}")
        return None, None

#monitor message
def monitor_messages(conn):
    last_message = ""

    while True:
        try:
            #get username and message
            username, latest_message = get_username_and_message()

            if username and latest_message:
                if latest_message != last_message:
                    print(f"New message detected from {username}: {latest_message}")
                    last_message = latest_message

                    #check if mention is from itself
                    if "@Aaliyah" in latest_message and username != "Aaliyah":
                        response = generate_response(conn, username, latest_message)
                        send_message(response)

            time.sleep(2)  #Check every 2 seconds
        except Exception as e:
            print(f"Error during message monitoring: {e}")

def send_message(message):
    try:

        sanitized_message = sanitize_message(message)
        
        message_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='markup_f8f345 editor_a552a6 slateTextArea_e52116 fontSize16Padding_d0696b']"))
        )
        message_box.click()

        print(user_memory)
        message_box.send_keys(sanitized_message)

        message_box.send_keys("\n")
        message_box.send_keys("\n")

    except Exception as e:
        print(f"Error while sending message: {e}")

def generate_response(conn, username, latest_message):
    try:
        #loadlast interaction
        conversation_history = load_memory(conn, username, limit=1)

        #prepare the conversation history
        user_history = ""
        if conversation_history:
            for user_message, bot_response in conversation_history:
                user_history += f"User: {user_message}\nAaliyah: {bot_response}\n"

        # Define the Ollama api
        ollama_url = "http://localhost:11434/api/generate"
        prompt = f"{character_personality}\nHere is the latest message from {username}:\nUser: {latest_message}\nAaliyah (Respond in short sentences and casual tone):"
        payload = {
            "model": "mistral",
            "prompt": prompt
        }

        #request
        response = requests.post(ollama_url, json=payload, stream=True)

        #Check if the request was successful
        if response.status_code != 200:
            print(f"API Request failed with status code: {response.status_code}")
            return "couldn't generate a response."

        full_response = ""
        #streaming
        for line in response.iter_lines():
            if line:
                try:
                    line_data = json.loads(line)
                    if 'response' in line_data:
                        full_response += line_data['response']

                    # Check if the response is done
                    if line_data.get('done', False):
                        break
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    return "couldn't understand the ai response."

        #save message to memory
        save_memory(conn, username, latest_message, full_response.strip())

        #return response
        return full_response.strip()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return "There was an issue communicating with the AI."

if __name__ == "__main__":
    conn = init_memory_db()
    discord_login(discord_email, discord_password)
    time.sleep(5)

    #Send opening message (chat name, message)
    send_test_message("Seige diamond 1 nigel farage", "yo im back")
    monitor_messages(conn)
