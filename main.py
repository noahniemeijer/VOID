import curses
import subprocess
import textwrap
import threading
from datetime import datetime
import time
import sys

def ask_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", "gemma3:1b"],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        if result.returncode == 0:
            response = result.stdout.decode("utf-8").strip()
            return response
        else:
            error_msg = result.stderr.decode("utf-8").strip()
            return f"Error: {error_msg}"
    except subprocess.TimeoutExpired:
        return "Error: Request timed out."
    except Exception as e:
        return f"Error: {str(e)}"

def reset_ai():
    subprocess.run(["ollama", "rm", "gemma3:1b"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["ollama", "pull", "gemma3:1b"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return "AI has been reset. Please run the program again."

def show_popup(stdscr, message):
    height, width = stdscr.getmaxyx()
    y = height // 2 - 1
    x = width // 2 - len(message) // 2
    stdscr.addstr(y, x, message, curses.A_BOLD)
    stdscr.refresh()
    time.sleep(2)

def add_bold_markup(stdscr, y, x, text):
    parts = text.split("**")
    bold = False
    cur_x = x
    for part in parts:
        if bold:
            stdscr.addstr(y, cur_x, part, curses.A_BOLD)
        else:
            stdscr.addstr(y, cur_x, part)
        cur_x += len(part)
        bold = not bold

def render_multiline_text_wrapped_lines(message_content, max_width):
    logical_lines = message_content.split('\n')

    all_wrapped_lines = []
    for line_segment in logical_lines:
        if not line_segment.strip() and all_wrapped_lines and all_wrapped_lines[-1] != "":
            all_wrapped_lines.append("")
            continue

        wrapped_parts = textwrap.wrap(line_segment, max_width) or [""]
        all_wrapped_lines.extend(wrapped_parts)

    return all_wrapped_lines

def chat_ui(stdscr):
    curses.curs_set(1)
    stdscr.clear()
    stdscr.timeout(100)
    height, width = stdscr.getmaxyx()

    chat_log = []
    input_text = ""
    lock = threading.Lock()
    scroll_offset = 0

    def get_prefix(name, timestamp_str):
        return f"[{timestamp_str}] {name}: "

    def fetch_response(prompt, idx_to_replace):
        nonlocal scroll_offset
        reply = ask_ollama(prompt)
        current_timestamp = datetime.now().strftime("%H:%M")
        with lock:
            chat_log[idx_to_replace] = ("Bot", reply, current_timestamp)
            scroll_offset = max(0, len(chat_log) - 1)

    while True:
        stdscr.clear()
        
        max_chat_display_rows = height - 3 

        message_row_counts = []
        for name, message_content, _ in chat_log:
            prefix_len = len(get_prefix(name, "HH:MM"))
            effective_content_width = width - 2 - prefix_len - 1
            wrapped_lines = render_multiline_text_wrapped_lines(message_content, effective_content_width)
            message_row_counts.append(len(wrapped_lines) if wrapped_lines else 1)
        
        possible_scroll_offset_for_bottom = 0
        if chat_log:
            current_rows_from_bottom = 0
            for i in range(len(chat_log) - 1, -1, -1):
                rows_for_msg = message_row_counts[i]
                current_rows_from_bottom += rows_for_msg
                if current_rows_from_bottom > max_chat_display_rows:
                    possible_scroll_offset_for_bottom = i + 1
                    break
        
        scroll_offset = max(0, min(scroll_offset, possible_scroll_offset_for_bottom))

        current_y = 0
        with lock:
            for i in range(scroll_offset, len(chat_log)):
                name, message_content, timestamp_str = chat_log[i]
                
                prefix = get_prefix(name, timestamp_str)
                
                effective_content_width = width - 2 - len(prefix) - 1
                
                wrapped_message_lines = render_multiline_text_wrapped_lines(message_content, effective_content_width)
                
                if wrapped_message_lines:
                    first_line_content = wrapped_message_lines[0]
                    
                    if current_y < max_chat_display_rows:
                        full_display_line = prefix + first_line_content
                        add_bold_markup(stdscr, current_y, 2, full_display_line)
                        current_y += 1
                    else:
                        break

                    for j in range(1, len(wrapped_message_lines)):
                        if current_y >= max_chat_display_rows:
                            break
                        line_to_render = wrapped_message_lines[j]
                        add_bold_markup(stdscr, current_y, 2 + len(prefix), line_to_render)
                        current_y += 1
                else:
                    if current_y < max_chat_display_rows:
                        add_bold_markup(stdscr, current_y, 2, prefix)
                        current_y += 1
                    else:
                        break

        stdscr.addstr(height - 2, 2, "> " + input_text[:width - 4])
        stdscr.refresh()

        key = stdscr.getch()
        if key == -1:
            continue

        if key == curses.KEY_UP:
            if scroll_offset > 0:
                scroll_offset -= 1
                time.sleep(0.05)
        elif key == curses.KEY_DOWN:
            if scroll_offset < possible_scroll_offset_for_bottom:
                scroll_offset += 1
                time.sleep(0.05)

        elif key == curses.KEY_PPAGE:
            lines_scrolled_up = 0
            temp_offset = scroll_offset
            while lines_scrolled_up < max_chat_display_rows and temp_offset > 0:
                temp_offset -= 1
                lines_scrolled_up += message_row_counts[temp_offset]
            scroll_offset = max(0, temp_offset)


        elif key == curses.KEY_NPAGE:
            lines_scrolled_down = 0
            temp_offset = scroll_offset
            while lines_scrolled_down < max_chat_display_rows and temp_offset < len(chat_log) - 1:
                lines_scrolled_down += message_row_counts[temp_offset]
                temp_offset += 1
            
            scroll_offset = min(temp_offset, possible_scroll_offset_for_bottom)


        elif key in (curses.KEY_BACKSPACE, 127):
            input_text = input_text[:-1]
        elif key == ord('\n'):
            if input_text.lower() == "/exit":
                break
            
            current_timestamp = datetime.now().strftime("%H:%M")
            with lock:
                chat_log.append(("You", input_text, current_timestamp))

                placeholder_index = len(chat_log)
                chat_log.append(("Bot", "...", current_timestamp))
                
                scroll_offset = max(0, len(chat_log) - 1) 

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
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  
    stdscr.bkgd(curses.color_pair(1)) 

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
            y = height // 2 + i
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
                exit()

if __name__ == "__main__":
    subprocess.run(["bash", "install.sh"], check=True)
    curses.wrapper(menu_ui)