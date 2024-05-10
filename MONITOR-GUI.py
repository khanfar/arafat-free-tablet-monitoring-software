import tkinter as tk
from tkinter import messagebox
from telegram.ext import Updater, MessageHandler, Filters
import threading
import queue
import winsound
from datetime import datetime
import os

DEFAULT_BOT_TOKEN = ""
DEFAULT_GROUP_CHAT_ID = ""
CONFIG_FILE = "config.txt"

def save_config(bot_token, group_chat_id):
    with open(CONFIG_FILE, "w") as file:
        file.write(f"{bot_token}\n")
        file.write(f"{group_chat_id}\n")

def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            bot_token = file.readline().strip()
            group_chat_id = file.readline().strip()
            return bot_token, group_chat_id
    except FileNotFoundError:
        return DEFAULT_BOT_TOKEN, DEFAULT_GROUP_CHAT_ID

# Maintain a set of unique vehicle numbers
unique_vehicle_numbers = set()

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'group_messages.txt')

def handle_message(update, context, group_chat_id):
    if update.message.chat_id == int(group_chat_id):
        messages = update.message.text.split('\n\n')  # Split messages by double newline
        for message in messages:
            # Extracting required fields from each message
            vehicle_number = None
            vehicle_type = None
            entry_date = None
            company_name = None
            mechanic_name = None

            # Splitting the message into lines and extracting the required fields
            for line in message.split('\n'):
                if line.startswith('رقم المركبة:'):
                    vehicle_number = line.split(': ')[1]
                elif line.startswith('نوع المركبه:'):
                    vehicle_type = line.split(': ')[1]
                elif line.startswith('تاريخ الدخول:'):
                    entry_date = line.split(': ')[1]
                elif line.startswith('اسم الشركه:'):
                    parts = line.split(': ')
                    if len(parts) > 1:
                        company_name = parts[1]
                elif line.startswith('اسم الميكانيكي:'):
                    mechanic_name = line.split(': ')[1]

            # Check if the vehicle number is already stored in the file
            if not is_duplicate_record(entry_date, vehicle_number):
                # Constructing the formatted message
                formatted_message = f"{entry_date} | "
                formatted_message += f"{vehicle_number} | "  # Include vehicle number
                formatted_message += f"اسم الشركه: {company_name} | "
                formatted_message += f"{vehicle_type} | "
                formatted_message += f"اسم الميكانيكي: {mechanic_name}\n"

                # Insert the formatted message into the terminal box
                terminal_box.insert(tk.END, formatted_message)

                # Beep sound
                winsound.Beep(1000, 100)

                # Forward the message to the group chat
                update.message.forward(chat_id=int(group_chat_id))

                # Write the formatted message to a file
                with open(file_path, 'a') as file:
                    file.write(formatted_message)

def is_duplicate_record(entry_date, vehicle_number):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(" | ")
                if len(parts) >= 2 and parts[0] == entry_date and parts[1] == vehicle_number:
                    return True
    except FileNotFoundError:
        pass
    return False


def start_bot():
    bot_token, group_chat_id = load_config()
    
    today_date = datetime.now().strftime("%B %d, %Y")  # Get today's date in the format Month Day, Year
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(" | ")
                if len(parts) == 5:  # Adjusted for the correct number of fields
                    # Extracting the date from the record
                    record_date = parts[0]
                    # Convert the record date string to a datetime object for comparison
                    record_datetime = datetime.strptime(record_date, "%B %d, %Y")
                    # Check if the record date matches today's date
                    if record_datetime.strftime("%B %d, %Y") == today_date:
                        # Extracting the company name
                        company_name_parts = parts[2].split(": ")
                        if len(company_name_parts) > 1:
                            company_name = company_name_parts[1]
                        else:
                            company_name = "Unknown"  # Default value if company name is not provided
                        # Construct the formatted message
                        formatted_message = f"{parts[0]} | {parts[1]} | اسم الشركه: {company_name} | {parts[3]} | {parts[4]}\n"
                        terminal_box.insert(tk.END, formatted_message)
    except FileNotFoundError:
        pass

    terminal_box.insert(tk.END, "نظام المراقبة قيد التشغيل\n")
    send_start_message(bot_token, group_chat_id)  # Sending start message
    start_button_ball.itemconfig(ball, fill="green")
    blink_ball()
    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher

    # Register handle_message with group_chat_id
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: handle_message(update, context, group_chat_id)))
    updater.start_polling()


def send_start_message(bot_token, group_chat_id):
    updater = Updater(token=bot_token)
    bot = updater.bot
    bot.send_message(chat_id=group_chat_id, text="The bot has started.")

def blink_ball():
    current_color = start_button_ball.itemcget(ball, "fill")
    new_color = "red" if current_color == "green" else "green"
    start_button_ball.itemconfig(ball, fill=new_color)
    root.after(1000, blink_ball)

def process_queue():
    while not message_queue.empty():
        message = message_queue.get()
        terminal_box.insert(tk.END, message)
    root.after(100, process_queue)

def save_config_callback():
    global bot_token_entry, group_chat_id_entry
    bot_token = bot_token_entry.get()
    group_chat_id = group_chat_id_entry.get()
    if bot_token and group_chat_id:
        save_config(bot_token, group_chat_id)
        messagebox.showinfo("Saved", "Configuration saved successfully.")
    else:
        messagebox.showwarning("Error", "Bot token and group chat ID cannot be empty.")

# Main application window
def open_bot_config_window():
    global bot_token_entry, group_chat_id_entry, config_window
    
    config_window = tk.Toplevel(root)
    config_window.title("تكوين الروبوت")
    config_window.geometry("400x200")
    
    bot_token_label = tk.Label(config_window, text="Bot Token:", font=("Arial", 14))
    bot_token_label.grid(row=0, column=0, padx=5, pady=5)
    bot_token_entry = tk.Entry(config_window, font=("Arial", 14), width=30)
    bot_token_entry.grid(row=0, column=1, padx=5, pady=5)

    group_chat_id_label = tk.Label(config_window, text="Group Chat ID:", font=("Arial", 14))
    group_chat_id_label.grid(row=1, column=0, padx=5, pady=5)
    group_chat_id_entry = tk.Entry(config_window, font=("Arial", 14), width=30)
    group_chat_id_entry.grid(row=1, column=1, padx=5, pady=5)

    load_config_button = tk.Button(config_window, text="Load Config", font=("Arial", 14), command=load_config_callback)
    load_config_button.grid(row=2, column=0, columnspan=2, pady=5)

    save_config_button = tk.Button(config_window, text="Save Config", font=("Arial", 14), command=save_config_callback)
    save_config_button.grid(row=3, column=0, columnspan=2, pady=5)

def load_config_callback():
    global bot_token_entry, group_chat_id_entry
    bot_token, group_chat_id = load_config()
    bot_token_entry.delete(0, tk.END)
    bot_token_entry.insert(0, bot_token)
    group_chat_id_entry.delete(0, tk.END)
    group_chat_id_entry.insert(0, group_chat_id)

root = tk.Tk()
root.title("شركة ابناء عرفات")
root.geometry("1024x768") # Adjusted GUI size for 12-inch screen
root.configure(bg="gray")

title_label = tk.Label(root, text="نظام تسجيل المركبات", font=("Arial", 20), bg="gray")
title_label.pack(pady=5)

terminal_frame = tk.Frame(root, height=500, width=900, bg="gray")
terminal_frame.pack(pady=10)

terminal_box = tk.Text(terminal_frame, wrap='word', bg='black', fg='green', font=("Arial", 16), height=25, width=110) # Increased font size to 16
terminal_box.pack(fill='both', expand=True)

start_bot_button = tk.Button(root, text="تشغيل", command=start_bot)
start_bot_button.pack(pady=5)

start_button_ball = tk.Canvas(root, width=60, height=60, bg="gray", highlightthickness=0)
start_button_ball.pack(pady=5)
ball = start_button_ball.create_oval(10, 10, 50, 50, fill="red")

message_queue = queue.Queue()
process_queue()

config_menu = tk.Menu(root)
root.config(menu=config_menu)
config_menu.add_command(label="Bot Configuration", command=open_bot_config_window)

root.mainloop()
