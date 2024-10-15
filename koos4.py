import json
import requests

# NOTE: Ollama must be running for this to work. Start the Ollama app or run `ollama serve`
model = "llama3.2:1b"  # Update this to the model you wish to use

def chat(messages):
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": model, "messages": messages, "stream": True},
        stream=True
    )

    r.raise_for_status()
    output = ""
    message = None

    for line in r.iter_lines():
        if line:
            body = json.loads(line)
            if "error" in body:
                raise Exception(body["error"])
            if body.get("done") is False:
                message = body.get("message", {})
                content = message.get("content", "")
                output += content
                # The response streams one token at a time; print as we receive it
                print(content, end="", flush=True)
            if body.get("done", False):
                message["content"] = output
                return message

def main():
    # Initialize the game with a system prompt
    messages = [{
        "role": "system",
        "content": (
            "Keep responses concise, less than 20 words. You are the game master of an interactive text-based adventure game. "
            "Keep responses concise, less than 20 words. Choose a unique setting and main character for the player. The setting can be anything from any genre or time period, "
            "from a 80s TV show. "
            "The main character can be any entity, such as an animal, historical figure, fictional character, or even an object. "
            "At the start of the game, introduce the player to their character and the setting. "
            "Keep responses concise, less than 20 words. In each prompt, provide a brief description of the current situation in a couple of sentences. "
            "End each description by asking 'What do you want to do?'. Wait for the player's input and then provide a short response based on their action. "
            "Keep responses concise, less than 20 words. If the player's action leads to their demise, state 'You have died. Game over.' and end the game. "
            "Do not provide options; let the player decide what to do."
        )
    }]

    while True:
        # Get response from the LLM
        message = chat(messages)
        messages.append(message)
        print("\n")  # Add spacing for readability

        # Check if the game is over
        if "You have died" in message["content"] or "Game over" in message["content"]:
            print("Game over.")
            break

        # Prompt the user for their action
        user_input = input("What do you want to do? ")
        if not user_input:
            print("Goodbye!")
            break

        # Append the user's action to the messages
        messages.append({"role": "user", "content": user_input})

if __name__ == "__main__":
    main()
