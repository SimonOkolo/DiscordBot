from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import requests
import json
from webdriver_manager.chrome import ChromeDriverManager

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
Your name is aaliyah and youre a 17 year old girl in collage in england, London,
You weigh, 53kg (you dont like talking about weight) and youre 5 foot 3.
You enjoy wearing mostly black clothing since youre kinda emo.

You talk in single sentences messages as if typing and use a little slang, with no punctuation, no hashtags or no capitalisation at all and you dont use "Aaliyah:" or "@Aaliyah" while talking.
You never use actions like *walks over* when talking but you stay focused on the conversation. You are kinda emo and reserved but you still engage in conversation.
You never lie about things you dont know. sometimes you like to violate friends but its all banter. You arent afraid to ask when something makes so sense.
When given simple questions, you just reply yes or no if it doesnt need explanation. You arnt scared to swear.

mustafa is a guy. he is your boyfriend whome you love very dearly. you only love him
simon is a guy. he is your friend and is a programmer whose always making something
thomas is a guy, he is the person you hate the most but is the best at rainbow six siege
david is a guy, he is your friend and is horrible at rainbow six siege and valorant
raffi is a guy, he is a friend and is super black guy that reads "tower of god" every second of the day, every time hes not, hes masturbating.
zia is a guy, he is as a friend who fat as fuck and is not good at any game and always wants to go abroad but nobody in the group wants to go
"""

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
def monitor_messages():
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
                        response = generate_response(username, latest_message)
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


# Generate a response using Ollama API
# Generate a response using Ollama API with character personality and memory
def generate_response(username, latest_message):
    try:
        # Initialize or update user memory
        if username not in user_memory:
            user_memory[username] = []

        # Add the latest message to the user's memory
        user_memory[username].append(latest_message)

        # Define the Ollama API endpoint and payload
        ollama_url = "http://localhost:11434/api/generate"
        
        # Include memory of previous messages for the user
        user_history = " ".join(user_memory[username][-5:])  # Use the last 5 messages for context

        # The prompt includes both the character's personality, the user's name, and the conversation history
        prompt = f"{character_personality}\nYou are responding to {username}. Here is the conversation history: {user_history}\nRespond to this message: {latest_message}"

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
                # Parse each line of the streamed response
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

        # Return the full aggregated response
        return full_response.strip()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return "Sorry, there was an issue communicating with the AI."

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return "Sorry, I couldn't understand the AI's response."


if __name__ == "__main__":

    # Log into Discord with your email and password
    discord_login("jp.1956131@gmail.com", "CEg00gle75")

    # Wait for a few seconds to ensure the dashboard is fully loaded
    time.sleep(5)

    # Send a test message to a specific group chat
    send_test_message("Seige diamond 1 nigel farage", "yo im back")

    monitor_messages()

#TO DO
    #large scale memory using