import curses
import subprocess
import textwrap
import threading
import requests
from datetime import datetime
import time
import sys

def run_install_script():
    try:
        subprocess.run(["bash", "install.sh"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running install.sh: {e}")
        exit(1)

def reset_ai():
    try:
        subprocess.Popen(["ollama", "rm", "gemma3:1b"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.Popen(["ollama", "pull", "gemma3:1b"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return f"Error during AI reset: {e}"

    return "AI has been reset. Please run the program again."

def show_popup(stdscr, message):
    height, width = stdscr.getmaxyx()
    y = height // 2 - 1
    x = width // 2 - len(message) // 2
    stdscr.addstr(y, x, message, curses.A_BOLD)
    stdscr.refresh()
    time.sleep(2)

def chat_ui(stdscr):
    curses.curs_set(1)
    stdscr.clear()
    stdscr.timeout(100)
    height, width = stdscr.getmaxyx()

    chat_log = []
    input_text = ""
    model = "gemma3:1b"
    lock = threading.Lock()

    try:
        requests.post("http://localhost:11434/api/reset", json={"model": model})
    except Exception as e:
        pass

    def wrap_message(name, message):
        timestamp = datetime.now().strftime("%H:%M")
        prefix = f"[{timestamp}] {name}: "
        wrap_width = width - len(prefix) - 4
        wrapped = textwrap.wrap(message, wrap_width)
        return [(prefix, wrapped[0])] + [(" " * len(prefix), line) for line in wrapped[1:]]

    def fetch_response(prompt, idx_to_replace):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "").strip()
                bot_lines = wrap_message("Bot", reply)
                with lock:
                    chat_log[idx_to_replace] = bot_lines
            else:
                with lock:
                    chat_log[idx_to_replace] = wrap_message("Error", f"Status code {response.status_code}")

        except Exception as e:
            with lock:
                chat_log[idx_to_replace] = wrap_message("Error", str(e))

    while True:
        stdscr.clear()
        y = 0

        with lock:
            for entry in chat_log:
                for prefix, line in entry:
                    if y >= height - 3:
                        break
                    stdscr.addstr(y, 2, prefix, curses.A_BOLD)
                    stdscr.addstr(y, 2 + len(prefix), "\t" + line)
                    y += 1

        stdscr.addstr(height - 2, 2, "> " + input_text[:width - 4])
        stdscr.refresh()

        key = stdscr.getch()
        if key == -1:
            continue

        if key in (curses.KEY_BACKSPACE, 127):
            input_text = input_text[:-1]
        elif key == ord('\n'):
            if input_text.lower() == "/bye":
                break
            elif input_text.lower() == "/clear":
                try:
                    requests.post("http://localhost:11434/api/reset", json={"model": model})
                    chat_log.append(wrap_message("System", "Context cleared.")[0:1])
                except Exception as e:
                    chat_log.append(wrap_message("Error", f"Clear failed: {str(e)}")[0:1])
                input_text = ""
                continue

            user_lines = wrap_message("You", input_text)
            with lock:
                chat_log.append(user_lines)

                placeholder = wrap_message("Bot", "...")
                chat_log.append(placeholder)
                placeholder_index = len(chat_log) - 1

            thread = threading.Thread(target=fetch_response, args=(input_text, placeholder_index))
            thread.daemon = True
            thread.start()

            input_text = ""
        elif 32 <= key <= 126:
            input_text += chr(key)

def settings_ui(stdscr):
    curses.curs_set(0)
    curses.mousemask(0)
    stdscr.clear()

    menu_items = ["Reset AI", "Back"]
    selected_idx = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "Settings"
        x = width // 2 - len(title) // 2
        y = height - 35
        stdscr.addstr(y, x, title, curses.A_BOLD)

        for i, text in enumerate(menu_items):
            x = width // 2 - len(text) // 2
            y = height - 33 + i
            if i == selected_idx:
                stdscr.addstr(y, x, text, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, text)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and selected_idx > 0:
            selected_idx -= 1
        elif key == curses.KEY_DOWN and selected_idx < len(menu_items) - 1:
            selected_idx += 1
        elif key == ord('\n'):
            if menu_items[selected_idx] == "Reset AI":
                message = reset_ai()
                show_popup(stdscr, message)
                sys.exit()  

            elif menu_items[selected_idx] == "Back":
                break

def menu_ui(stdscr):
    curses.curs_set(0)
    curses.mousemask(0)
    stdscr.clear()

    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Set color pair for white text on black background
    stdscr.bkgd(curses.color_pair(1))  # Set background to black

    menu_items = ["Start", "Settings", "Quit"]
    selected_idx = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "VOID MENU"
        x = width // 2 - len(title) // 2
        y = height - 35
        stdscr.addstr(y, x, title, curses.A_BOLD)

        for i, text in enumerate(menu_items):
            x = width // 2 - len(text) // 2
            y = height - 33 + i
            if i == selected_idx:
                stdscr.addstr(y, x, text, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, text)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and selected_idx > 0:
            selected_idx -= 1
        elif key == curses.KEY_DOWN and selected_idx < len(menu_items) - 1:
            selected_idx += 1
        elif key == ord('\n'):
            if menu_items[selected_idx] == "Start":
                chat_ui(stdscr)
            elif menu_items[selected_idx] == "Settings":
                settings_ui(stdscr)
            elif menu_items[selected_idx] == "Quit":
                break


if __name__ == "__main__":
    curses.wrapper(menu_ui)
