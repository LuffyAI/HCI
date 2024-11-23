import requests
import pandas as pd

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
            return messages  # Return messages to be used elsewhere
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_all_messages():
    """
    Deletes all messages from the FastAPI server.
    """
    url = f"{BASE_URL}/delete_messages/"
    try:
        response = requests.delete(url)
        if response.status_code == 200:
            print(response.json().get("status", "Messages deleted successfully!"))
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"An error occurred: {e}")

def save_messages_to_excel():
    """
    Saves the retrieved messages to an Excel file.
    """
    messages = get_messages()
    if not messages:
        print("No messages to save.")
        return

    # Convert messages to a DataFrame
    data = [{"Sender": "You" if msg["sender"] == "user" else "Other User", "Message": msg["text"]} for msg in messages]
    df = pd.DataFrame(data)

    # Get the filename from the user
    filename = input("Enter the name of the Excel file to save (without extension): ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return

    # Save to Excel
    try:
        filepath = f"{filename}.xlsx"
        df.to_excel(filepath, index=False)
        print(f"Messages saved successfully to {filepath}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

def main():
    """
    Main function to provide terminal interface.
    """
    print("Welcome to the Terminal Messenger!")
    while True:
        print("\nOptions:")
        print("1. Send a message as 'Other User'")
        print("2. View all messages")
        print("3. Delete all messages")
        print("4. Save messages to Excel")
        print("5. Exit")
        choice = input("Enter your choice (1/2/3/4/5): ").strip()
        
        if choice == "1":
            text = input("Enter the message to send: ").strip()
            send_message("other", text)
        elif choice == "2":
            get_messages()
        elif choice == "3":
            delete_all_messages()
        elif choice == "4":
            save_messages_to_excel()
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
