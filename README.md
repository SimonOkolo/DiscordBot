
# Discord Bot

This python program allows you to use a locally hosted AI (using ollama) to run a real discord account (not a bot account), able to respond to messages when mentioned in the chat.

This is for educational purposes since it goes against discords TOS (selfbot), do not use in public servers/groupchats.

##

WARNING:
This will get the account banned if discord detects too many requests, use chrome profiles to minimise the amount of login requests, and dont abuse.



## How it works

1. Uses selenium to check for new messages in the div every two seconds
2. Extracts the message if the account is mentioned
3. Message is taken and put throught the ai (in this example mixtral7b)
4. Response is generated and entered in the chat div
