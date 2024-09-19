from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up the Chrome browser
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-infobars')  # Disable pop-ups and infobars
options.add_argument('--start-maximized')  # Start maximized for visibility

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Login function
def discord_login(email, password):
    driver.get("https://discord.com/login")

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
def monitor_messages():
    last_message = ""

    while True:
        try:
            # Get the list of messages (You may need to adjust this CSS selector)
            messages = driver.find_elements(By.CSS_SELECTOR, "div[class*='messageContent']")

            # If there are messages, get the latest one
            if messages:
                latest_message = messages[-1].text

                # If the latest message is new (not the same as the last message), process it
                if latest_message != last_message:
                    print(f"New message detected: {latest_message}")
                    last_message = latest_message

                    # Check if the bot's username is mentioned
                    if "@★❣aaliyah❣★" in latest_message:
                        response = generate_response(latest_message)
                        send_message(response)

            time.sleep(2)  # Check every 2 seconds
        except Exception as e:
            print(f"Error during message monitoring: {e}")

# Send a message in response to a mention
def send_message(message):
    try:
        message_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='markup_f8f345 editor_a552a6 slateTextArea_e52116 fontSize16Padding_d0696b']"))
        )
        message_box.click()

        #Type the message
        message_box.send_keys(message)

        # Simulate pressing Enter to send the message
        message_box.send_keys("\n")
        message_box.send_keys("\n")
    except Exception as e:
        print(f"Error while sending message: {e}")


# Generate an AI response (dummy function for now)
def generate_response(latest_message):
    message_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='markup_f8f345 editor_a552a6 slateTextArea_e52116 fontSize16Padding_d0696b']"))
    )
    if latest_message == "@★❣aaliyah❣★":
            message_box.send_keys("if this is thomas you can fucking kys")
            message_box.send_keys("\n")

    return f"Responding to: {latest_message}"


if __name__ == "__main__":

    # Log into Discord with your email and password
    discord_login("jordanbennett.7158@gmail.com", "CEg00gle75")

    # Wait for a few seconds to ensure the dashboard is fully loaded
    time.sleep(5)

    # Send a test message to a specific group chat
    send_test_message("Seige diamond 1 nigel farage", "active")

    monitor_messages()

#TO DO
#username specific responses
#ollama ai api implementation
    #large scale memory using