import requests
import pandas as pd

BASE_URL = "http://45.76.22.199:8000"

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
                timestamp = msg.get("timestamp", "No timestamp available")
                print(f"[{timestamp}] {sender}: {msg['text']}")

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
    Saves the retrieved messages and suggestion statistics to an Excel file.
    """
    # Retrieve messages
    messages = get_messages()
    if not messages:
        print("No messages to save.")
        return

    # Retrieve suggestion statistics
    suggestion_stats = get_suggestion_stats()
    if not suggestion_stats:
        print("No suggestion statistics to save.")
        return

    # Prepare messages data for saving
    message_data = [
        {
            "Timestamp": msg.get("timestamp", "No timestamp available"),
            "Sender": "You" if msg["sender"] == "user" else "Other User",
            "Message": msg["text"]
        }
        for msg in messages
    ]
    message_df = pd.DataFrame(message_data)

    # Prepare suggestion stats data for saving
    suggestion_data = [
        {
            "Suggestion": entry["suggestion"],
            "Status": "Used" if entry["used"] else "Not Used"
        }
        for entry in suggestion_stats.get('history', [])
    ]
    suggestion_df = pd.DataFrame(suggestion_data)

    # Prepare total suggestion stats summary
    summary_data = {
        "Total Suggestions Used": [suggestion_stats.get("total_suggestions", 0)],
        "Total Suggestions Number": [suggestion_stats.get("total_number_of_suggestions", 0)]
    }
    summary_df = pd.DataFrame(summary_data)

    # Get the filename from the user
    filename = input("Enter the name of the Excel file to save (without extension): ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return

    # Save data to Excel
    try:
        filepath = f"{filename}.xlsx"
        with pd.ExcelWriter(filepath) as writer:
            message_df.to_excel(writer, sheet_name="Messages", index=False)
            suggestion_df.to_excel(writer, sheet_name="Suggestion Stats", index=False)
            summary_df.to_excel(writer, sheet_name="Suggestion Summary", index=False)
        print(f"Messages and suggestion stats saved successfully to {filepath}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

def get_suggestion_stats():
    """
    Retrieves suggestion statistics from the FastAPI server.
    """
    url = f"{BASE_URL}/get_suggestion_stats/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            stats = response.json()
            print("\nSuggestion Stats:")
            print(f"Total Suggestions Used: {stats['total_suggestions']}")
            print(f"Total Suggestions Number: {stats['total_number_of_suggestions']}")
            print("\nHistory of Suggestions:")
            for entry in stats['history']:
                status = "Used" if entry["used"] else "Not Used"
                print(f"Suggestion: {entry['suggestion']}, Status: {status}")
            return stats
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

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
        print("5. Get suggestion stats")
        print("6. Exit")
        choice = input("Enter your choice (1/2/3/4/5/6): ").strip()
        
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
            get_suggestion_stats()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
