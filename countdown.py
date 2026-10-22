import ctypes
import json
import math
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox


SAVE_FILE = Path(__file__).with_name("countdown_data.json")
BACKGROUND = "black"
FOREGROUND = "white"
CONTROL_BACKGROUND = "#202020"
WATCH_SIZE = 190
WATCH_GAP = 205
TRANSPARENT_COLOR = "#010101"
WATCH_BACKGROUND = "#000000"
WATCH_RING = "#f6c94a"
WATCH_MARK = "#d6b84f"
WATCH_HAND = "#f5d36b"

root = tk.Tk()
root.withdraw()
events = []
countdown_labels = []
event_windows = {}


def save_events():
    SAVE_FILE.write_text(json.dumps({"events": events}, indent=2), encoding="utf-8")


def set_title_bar_colors(window):
    window.update_idletasks()
    window_handle = ctypes.windll.user32.GetParent(window.winfo_id())
    black = ctypes.c_int(0x00000000)
    white = ctypes.c_int(0x00FFFFFF)
    dwmapi = ctypes.windll.dwmapi
    dwmapi.DwmSetWindowAttribute(window_handle, 35, ctypes.byref(black), ctypes.sizeof(black))
    dwmapi.DwmSetWindowAttribute(window_handle, 36, ctypes.byref(white), ctypes.sizeof(white))


def remaining_parts(selected_date):
    total_seconds = max(0, int((selected_date - datetime.now()).total_seconds()))
    days_left, remainder = divmod(total_seconds, 86400)
    hours_left, remainder = divmod(remainder, 3600)
    minutes_left, seconds_left = divmod(remainder, 60)
    return days_left, hours_left, minutes_left, seconds_left


def update_countdowns():
    expired = []
    now = datetime.now()
    for event, labels in countdown_labels:
        due_date = datetime.fromisoformat(event["date"])
        if due_date <= now:
            expired.append(event)
            continue
        parts = remaining_parts(due_date)
        update_watch(labels, parts)
    for event in expired:
        events.remove(event)
        window = event_windows.pop(id(event), None)
        if window is root:
            for child in root.winfo_children():
                child.destroy()
            root.withdraw()
        elif window is not None:
            window.destroy()
        countdown_labels[:] = [item for item in countdown_labels if item[0] is not event]
        save_events()
    if expired:
        render_events()
        for event in expired:
            show_due_popup(event)
    root.after(1000, update_countdowns)


def remove_event(event, window):
    events.remove(event)
    event_windows.pop(id(event), None)
    if window is root:
        root.withdraw()
    else:
        window.destroy()
    save_events()


def update_watch(canvas, parts):
    days, hours, minutes, seconds = parts
    canvas.itemconfigure("days", text=f"{days:02d}")
    canvas.itemconfigure("hours", text=f"{hours:02d}")
    canvas.itemconfigure("minutes", text=f"{minutes:02d}")
    canvas.itemconfigure("seconds", text=f"{seconds:02d}")

    center = WATCH_SIZE / 2
    hand_length = WATCH_SIZE * 0.31
    minute_angle = ((minutes + seconds / 60) / 60) * 2 * 3.141592653589793
    hour_angle = ((hours % 12 + minutes / 60) / 12) * 2 * 3.141592653589793
    second_angle = (seconds / 60) * 2 * 3.141592653589793

    def hand(angle, length):
        return (center + length * math.sin(angle),
                center - length * math.cos(angle))

    for tag, angle, length, width in (
        ("hour-hand", hour_angle, hand_length * 0.7, 3),
        ("minute-hand", minute_angle, hand_length, 2),
        ("second-hand", second_angle, hand_length * 1.05, 1),
    ):
        end_x, end_y = hand(angle, length)
        canvas.coords(tag, center, center, end_x, end_y)


def open_watch_menu(event, countdown_event, window):
    menu = tk.Menu(window, tearoff=False, bg=CONTROL_BACKGROUND, fg=FOREGROUND,
                   activebackground="#404040", activeforeground=FOREGROUND)
    menu.add_command(label="Add event", command=show_add_event)
    menu.add_command(label="Remove event", command=lambda: remove_event(countdown_event, window))
    menu.tk_popup(event.x_root, event.y_root)


def start_drag(event, window):
    window._drag_start = (event.x_root, event.y_root,
                          window.winfo_x(), window.winfo_y())


def drag_watch(event, window):
    start_x, start_y, window_x, window_y = window._drag_start
    window.geometry(f"+{window_x + event.x_root - start_x}+{window_y + event.y_root - start_y}")


def open_event_window(event, index):
    window = root if index == 0 else tk.Toplevel(root)
    event_windows[id(event)] = window
    if window is root:
        root.deiconify()
    window.overrideredirect(True)
    window.attributes("-transparentcolor", TRANSPARENT_COLOR)
    window.geometry(f"{WATCH_SIZE}x{WATCH_SIZE}+20+{20 + index * WATCH_GAP}")
    window.resizable(False, False)
    canvas = tk.Canvas(window, width=WATCH_SIZE, height=WATCH_SIZE,
                       bg=TRANSPARENT_COLOR, highlightthickness=0)
    canvas.pack()
    pad = 4
    canvas.create_oval(pad, pad, WATCH_SIZE - pad, WATCH_SIZE - pad,
                       fill=WATCH_BACKGROUND, outline="")
    canvas.create_oval(pad, pad, WATCH_SIZE - pad, WATCH_SIZE - pad,
                       outline=WATCH_RING, width=3)
    canvas.create_oval(pad + 7, pad + 7, WATCH_SIZE - pad - 7, WATCH_SIZE - pad - 7,
                       outline="#806c2d", width=1)
    center = WATCH_SIZE / 2
    radius = WATCH_SIZE * 0.41
    for tick in range(12):
        angle = tick * 2 * math.pi / 12
        inner = radius - (8 if tick % 3 else 11)
        canvas.create_line(center + inner * math.sin(angle),
                           center - inner * math.cos(angle),
                           center + radius * math.sin(angle),
                           center - radius * math.cos(angle),
                           fill=WATCH_MARK, width=2 if tick % 3 == 0 else 1)
    for tag, width in (("hour-hand", 3), ("minute-hand", 2), ("second-hand", 1)):
        canvas.create_line(center, center, center, center - 1,
                           fill=WATCH_HAND if tag != "second-hand" else "#f0a63a",
                           width=width, tags=tag)
    canvas.create_oval(center - 3, center - 3, center + 3, center + 3,
                       fill=WATCH_HAND, outline="", tags="pin")

    labels = canvas
    value_y = center + 22
    value_x = (center - 57, center - 19, center + 19, center + 57)
    tags = ("days", "hours", "minutes", "seconds")
    for x, tag in zip(value_x, tags):
        canvas.create_text(x, value_y, text="00", fill=FOREGROUND,
                           font=("Consolas", 11, "bold"), tags=tag)
    canvas.create_text(center, value_y + 15, text="DAYS   HOURS  MINUTES  SECONDS",
                       fill="#aab5bd", font=("Arial", 5, "bold"))
    canvas.create_text(14, WATCH_SIZE - 13, text="+", fill=WATCH_RING,
                       font=("Arial", 13, "bold"), tags="add")
    canvas.create_text(WATCH_SIZE - 14, WATCH_SIZE - 13, text="×", fill="#ff7777",
                       font=("Arial", 13, "bold"), tags="remove")
    canvas.tag_bind("add", "<Button-1>", lambda _: show_add_event())
    canvas.tag_bind("remove", "<Button-1>", lambda _: remove_event(event, window))
    canvas.bind("<Button-3>", lambda click: open_watch_menu(click, event, window))
    canvas.bind("<Double-Button-1>", lambda _: show_add_event())
    canvas.bind("<ButtonPress-1>", lambda click: start_drag(click, window))
    canvas.bind("<B1-Motion>", lambda click: drag_watch(click, window))
    countdown_labels.append((event, labels))
    update_watch(canvas, remaining_parts(datetime.fromisoformat(event["date"])))


def show_due_popup(event):
    popup = tk.Toplevel(root)
    popup.title("Countdown finished")
    popup.geometry("360x190+490+250")
    popup.resizable(False, False)
    popup.configure(background=BACKGROUND)
    popup.transient(root)
    popup.grab_set()

    tk.Label(popup, text="The due is over have you done the work??",
             font=("Arial", 12, "bold"), bg=BACKGROUND,
             fg=FOREGROUND, wraplength=330).pack(pady=(18, 10))
    tk.Label(popup, text="Your response", bg=BACKGROUND,
             fg=FOREGROUND).pack(anchor="w", padx=18)
    response = tk.Text(popup, width=38, height=4, bg=CONTROL_BACKGROUND,
                       fg=FOREGROUND, insertbackground=FOREGROUND,
                       relief="flat")
    response.pack(padx=18, pady=(3, 8))
    tk.Button(popup, text="Close", command=popup.destroy,
              bg=CONTROL_BACKGROUND, fg=FOREGROUND,
              activebackground="#404040", activeforeground=FOREGROUND).pack()
    response.focus_set()
    popup.after_idle(lambda: set_title_bar_colors(popup))


def render_events():
    for event, labels in countdown_labels:
        window = labels[0].winfo_toplevel()
        if window is root:
            root.withdraw()
        else:
            window.destroy()
    countdown_labels.clear()
    event_windows.clear()

    if not events:
        root.deiconify()
        root.overrideredirect(True)
        root.attributes("-transparentcolor", TRANSPARENT_COLOR)
        root.geometry(f"{WATCH_SIZE}x{WATCH_SIZE}+20+20")
        root.resizable(False, False)
        canvas = tk.Canvas(root, width=WATCH_SIZE, height=WATCH_SIZE,
                           bg=TRANSPARENT_COLOR, highlightthickness=0)
        canvas.pack()
        canvas.create_oval(4, 4, WATCH_SIZE - 4, WATCH_SIZE - 4,
                           fill=WATCH_BACKGROUND, outline="")
        canvas.create_oval(4, 4, WATCH_SIZE - 4, WATCH_SIZE - 4,
                           outline=WATCH_RING, width=3)
        canvas.create_text(WATCH_SIZE / 2, WATCH_SIZE / 2 - 8, text="+",
                           fill=WATCH_RING, font=("Arial", 30, "bold"))
        canvas.create_text(WATCH_SIZE / 2, WATCH_SIZE / 2 + 25,
                           text="ADD EVENT", fill=FOREGROUND,
                           font=("Arial", 8, "bold"))
        canvas.bind("<Button-1>", lambda _: show_add_event())
        canvas.bind("<Double-Button-1>", lambda _: show_add_event())
        return

    for index, event in enumerate(events):
        open_event_window(event, index)


def show_add_event():
    dialog = tk.Toplevel(root)
    dialog.title("Add countdown event")
    dialog.geometry("300x260+490+20")
    dialog.resizable(False, False)
    dialog.configure(background=BACKGROUND)

    name = tk.StringVar()
    today = datetime.now()
    day = tk.StringVar(value=str(today.day))
    month = tk.StringVar(value=str(today.month))
    year = tk.StringVar(value=str(today.year))
    tk.Label(dialog, text="Event name", bg=BACKGROUND, fg=FOREGROUND).pack(
        anchor="w", padx=14, pady=(10, 1))
    name_entry = tk.Entry(dialog, textvariable=name, width=28, bg=CONTROL_BACKGROUND,
                          fg=FOREGROUND, insertbackground=FOREGROUND)
    name_entry.pack(padx=14)
    tk.Label(dialog, text="Event date", bg=BACKGROUND, fg=FOREGROUND).pack(
        anchor="w", padx=14, pady=(7, 1))
    date_frame = tk.Frame(dialog, bg=BACKGROUND)
    date_frame.pack()
    for variable, options in ((day, range(1, 32)), (month, range(1, 13)),
                              (year, range(today.year, today.year + 11))):
        menu = tk.OptionMenu(date_frame, variable, *[str(value) for value in options])
        menu.config(bg=CONTROL_BACKGROUND, fg=FOREGROUND,
                    activebackground="#404040", activeforeground=FOREGROUND)
        menu["menu"].config(bg=CONTROL_BACKGROUND, fg=FOREGROUND)
        menu.pack(side="left", padx=3)

    tk.Label(dialog, text="Event time (24-hour)", bg=BACKGROUND,
             fg=FOREGROUND).pack(anchor="w", padx=14, pady=(7, 1))
    hour = tk.StringVar(value=f"{today.hour:02d}")
    minute = tk.StringVar(value=f"{today.minute:02d}")
    time_frame = tk.Frame(dialog, bg=BACKGROUND)
    time_frame.pack()
    for variable, options in ((hour, range(24)), (minute, range(60))):
        menu = tk.OptionMenu(time_frame, variable, *[f"{value:02d}" for value in options])
        menu.config(bg=CONTROL_BACKGROUND, fg=FOREGROUND,
                    activebackground="#404040", activeforeground=FOREGROUND)
        menu["menu"].config(bg=CONTROL_BACKGROUND, fg=FOREGROUND)
        menu.pack(side="left", padx=3)

    def add_event():
        if not name.get().strip():
            messagebox.showerror("Missing event name", "Please enter an event name.", parent=dialog)
            return
        try:
            selected_date = datetime(int(year.get()), int(month.get()), int(day.get()),
                                     int(hour.get()), int(minute.get()))
        except ValueError:
            messagebox.showerror("Invalid date", "Please select a valid date.", parent=dialog)
            return
        if selected_date <= datetime.now():
            messagebox.showerror("Date has passed", "Please select a future date.", parent=dialog)
            return
        events.append({"name": name.get().strip(), "date": selected_date.isoformat()})
        save_events()
        dialog.destroy()
        render_events()

    tk.Button(dialog, text="Add event", command=add_event, bg=CONTROL_BACKGROUND,
              fg=FOREGROUND, activebackground="#404040", activeforeground=FOREGROUND).pack(pady=8)
    name_entry.focus_set()
    dialog.after_idle(lambda: set_title_bar_colors(dialog))


def restore_saved_events():
    try:
        saved = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        loaded = saved.get("events", [saved]) if isinstance(saved, dict) else []
        for event in loaded:
            selected_date = datetime.fromisoformat(event["date"])
            name = event["name"].strip()
            if name and selected_date > datetime.now():
                events.append({"name": name, "date": selected_date.isoformat()})
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    render_events()


restore_saved_events()
update_countdowns()
try:
    root.mainloop()
except KeyboardInterrupt:
    root.destroy()
