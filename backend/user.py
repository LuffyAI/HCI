import requests

BASE_URL = "http://localhost:8000"

def send_message(sender: str, text: str):
    """
    Sends a message to the FastAPI server.
    """
    url = f"{BASE_URL}/send_message/"
    payload = {"sender": sender, "text": text}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_messages():
    """
    Retrieves all messages from the FastAPI server.
    """
    url = f"{BASE_URL}/get_messages/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            messages = response.json()
            print("\nMessage History:")
            for msg in messages:
                sender = "You" if msg["sender"] == "user" else "Other User"
                print(f"{sender}: {msg['text']}")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    """
    Main function to provide terminal interface.
    """
    print("Welcome to the Terminal Messenger!")
    while True:
        print("\nOptions:")
        print("1. Send a message as 'Other User'")
        print("2. View all messages")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == "1":
            text = input("Enter the message to send: ").strip()
            send_message("other", text)
        elif choice == "2":
            get_messages()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
