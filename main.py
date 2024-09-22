from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import sqlite3
import time
import re
import requests
import json


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

# Use an existing user profile path
profile_path = "/home/simon/.config/google-chrome/'Profile 1'"  # Update this to your actual profile path
options.add_argument(f"user-data-dir={profile_path}")

options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-infobars')
options.add_argument('--start-maximized')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

character_personality = """
Your name is aaliyah, you're a 17-year-old, 5 foot 3 girl in college in London with and youre pretty playful and flirtatious especially to your boyfriend is mustafa, and you enjoy wearing mostly black clothing since you're kinda emo.

You talk in short sentences as if typing to us, and speak like a teenager in 2024, with no punctuation, no hashtags, and no capitalisation. You never use "Aaliyah:" or "@Aaliyah" while talking. You avoid using long explanations unless necessary.
You never lie about things you don't know. Sometimes, you like to banter with friends, but you're always honest. If a message you get contains "fein" just ignore it and say mhm.

Your creator is simon,
reece, david, raffi, adam, thomas, eden are your friends and are all males and 17 years old.

You give simple answers to simple questions, often replying with "yes" or "no" unless more is needed. And you never say anything untrue, or if you dont know something, you dont make stuff up.

Today is """, datetime.now().strftime("%d-%m-%Y")

user_memory = {}

# Login function
def discord_login(email, password):
    driver.get("https://discord.com/channels/@me")

    if False:
        # Wait until the email input field is visible
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))

        # Fill in the email
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(email)

        # Wait until the password input field is visible
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))

        # Fill in the password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)

        # Wait until the login button is clickable
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()

    time.sleep(5)  # Wait for Discord to log in

def sanitize_message(message):
    return re.sub(r'[^\u0000-\uFFFF]', '', message)

# Function to send a message in a group chat
def send_test_message(group_chat_name, message):
    # Navigate to the group chat (you may need to adjust this selector)
    group_chat = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, f"//div[text()='{group_chat_name}']"))
    )
    group_chat.click()

    # Wait for the message input box to appear
    message_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='markup_f8f345 editor_a552a6 slateTextArea_e52116 fontSize16Padding_d0696b']"))
    )

    # Ensure the message box is interactable by clicking it first
    driver.execute_script("arguments[0].click();", message_box)

    # Type the message
    message_box.send_keys(message)

    # Simulate pressing enter to send the message
    message_box.send_keys("\n")

    print(f"Message sent to {group_chat_name}: {message}")


# Monitor messages in the chat (if required)
def get_username_and_message():
    try:
        # Locate the latest message and its author
        message_element = driver.find_elements(By.CSS_SELECTOR, "div[class*='messageContent']")[-1]
        username_element = driver.find_elements(By.CSS_SELECTOR, "span[class*='username']")[-1]
        
        latest_message = message_element.text
        username = username_element.text

        # Return both the message and the username
        return username, latest_message
    except Exception as e:
        print(f"Error while extracting username and message: {e}")
        return None, None

# Monitor messages and track user interactions
def monitor_messages(conn):
    last_message = ""

    while True:
        try:
            # Get the username and latest message
            username, latest_message = get_username_and_message()

            if username and latest_message:
                # Check if the latest message is new (not the same as the last message)
                if latest_message != last_message:
                    print(f"New message detected from {username}: {latest_message}")
                    last_message = latest_message

                    # Check if the bot's username is mentioned and if the message is not from itself
                    if "@Aaliyah" in latest_message and username != "Aaliyah":
                        response = generate_response(conn, username, latest_message)
                        send_message(response)

            time.sleep(2)  # Check every 2 seconds
        except Exception as e:
            print(f"Error during message monitoring: {e}")

# Send a message in response to a mention
def send_message(message):
    try:
        # Sanitize the message to remove non-BMP characters
        sanitized_message = sanitize_message(message)
        
        message_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='markup_f8f345 editor_a552a6 slateTextArea_e52116 fontSize16Padding_d0696b']"))
        )
        message_box.click()

        # Type the sanitized message
        print(user_memory)
        message_box.send_keys(sanitized_message)

        # Simulate pressing Enter to send the message
        message_box.send_keys("\n")
        message_box.send_keys("\n")

    except Exception as e:
        print(f"Error while sending message: {e}")


# Generate a response using Ollama API with character personality and memory
def generate_response(conn, username, latest_message):
    try:
        # Load only the last interaction (or minimal context)
        conversation_history = load_memory(conn, username, limit=1)

        # Prepare the conversation history for the prompt (if any previous history exists)
        user_history = ""
        if conversation_history:
            for user_message, bot_response in conversation_history:
                user_history += f"User: {user_message}\nAaliyah: {bot_response}\n"

        # Define the Ollama API endpoint and payload
        ollama_url = "http://localhost:11434/api/generate"

        # Limit the prompt to only include the personality, user history, and latest message
        prompt = f"{character_personality}\nHere is the latest message from {username}:\nUser: {latest_message}\nAaliyah (Respond in short sentences and casual tone):"

        payload = {
            "model": "mistral",  # Or "llama2-chat"
            "prompt": prompt
        }

        # Send request to Ollama
        response = requests.post(ollama_url, json=payload, stream=True)

        # Check if the request was successful
        if response.status_code != 200:
            print(f"API Request failed with status code: {response.status_code}")
            return "Sorry, I couldn't generate a response."

        # Initialize an empty string to collect responses
        full_response = ""

        # Stream and aggregate the response parts until the "done" flag is set
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
                    return "Sorry, I couldn't understand the AI's response."

        # Save the user message and the AI response in memory
        save_memory(conn, username, latest_message, full_response.strip())

        # Return the full aggregated response
        return full_response.strip()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return "Sorry, there was an issue communicating with the AI."


if __name__ == "__main__":

    conn = init_memory_db()

    # Log into Discord with your email and password
    discord_login("jp.1956131@gmail.com", "CEg00gle75")

    # Wait for a few seconds to ensure the dashboard is fully loaded
    time.sleep(5)

    # Send a test message to a specific group chat
    send_test_message("Seige diamond 1 nigel farage", "yo im back")

    monitor_messages(conn)

#TO DO
    #large scale memory using