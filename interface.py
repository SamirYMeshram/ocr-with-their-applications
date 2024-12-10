import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font

# Functions to handle script execution
import subprocess

def open_geminiocr():
    subprocess.Popen(["python", "Gemini_OCR_SDK.py"])
    messagebox.showinfo("Action", "Enhanced OCR is starting...")

def open_simpleocr():
    subprocess.Popen(["python", "simpleocr.py"])
    messagebox.showinfo("Action", "Simple OCR is starting...")

def open_de():
    subprocess.Popen(["python", "de.py"])
    messagebox.showinfo("Action", "PDF to Audiobook is starting...")

def open_pdftrans():
    subprocess.Popen(["python", "pdftrans.py"])
    messagebox.showinfo("Action", "PDF Translation is starting...")

def exit_fullscreen():
    root.attributes("-fullscreen", False)
    root.geometry("800x600")  # Default size after exiting full screen

# Initialize the main tkinter window
root = tk.Tk()
root.title("Ultimate Feature Launcher")
root.attributes("-fullscreen", True)
root.configure(bg="#2c3e50")

# Fonts
font_header = Font(family="Helvetica", size=36, weight="bold")
font_subtitle = Font(family="Helvetica", size=16, slant="italic")
font_button = Font(family="Helvetica", size=20, weight="bold")
font_footer = Font(family="Helvetica", size=14)

# Header Section
header_frame = tk.Frame(root, bg="#34495e")
header_frame.pack(fill=tk.X, pady=10)

header_label = tk.Label(
    header_frame,
    text="🌟 Welcome to the Ultimate Feature of OCR 🌟",
    font=font_header,
    fg="white",
    bg="#34495e",
    pady=20
)
header_label.pack()

sub_label = tk.Label(
    header_frame,
    text="Choose a feature to get started",
    font=font_subtitle,
    fg="#ecf0f1",
    bg="#34495e"
)
sub_label.pack()

# Button Frame
button_frame = tk.Frame(root, bg="#2c3e50")
button_frame.pack(expand=True)

def create_button(parent, text, command):
    def on_enter(e):
        btn["background"] = "#e74c3c"

    def on_leave(e):
        btn["background"] = "#c0392b"

    btn = tk.Button(
        parent,
        text=text,
        font=font_button,
        bg="#c0392b",
        fg="white",
        activebackground="#e74c3c",
        activeforeground="white",
        command=command,
        width=25,
        height=2,
        relief="raised",
        bd=5
    )
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.pack(pady=15)
    return btn

# Reordered buttons:
create_button(button_frame, "✨ Enhanced OCR (Gemini AI)", open_geminiocr)
create_button(button_frame, "🔍 Simple OCR (EasyOCR)", open_simpleocr)
create_button(button_frame, "🎧 PDF to Audiobook", open_de)
create_button(button_frame, "📄 PDF Translation", open_pdftrans)

# Footer Section
footer_frame = tk.Frame(root, bg="#34495e")
footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

footer_label = tk.Label(
    footer_frame,
    text="Press 'Esc' to Exit Full Screen",
    font=font_footer,
    fg="#ecf0f1",
    bg="#34495e",
    pady=10
)
footer_label.pack()

# Bind Esc to exit full screen
root.bind("<Escape>", lambda e: exit_fullscreen())

# Start the tkinter event loop
root.mainloop()
