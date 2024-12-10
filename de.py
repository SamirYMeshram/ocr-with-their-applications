import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pdf2image
import pyttsx3
import easyocr
import pdfplumber
from playsound import playsound
import re
import numpy as np

# Function to extract text from PDF using pdfplumber
def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract text from PDF: {e}")
        return ""

# Function to convert PDF to image for OCR
def pdf_to_image(pdf_path):
    try:
        images = pdf2image.convert_from_path(pdf_path)
        if not images:
            raise ValueError("No images were returned from PDF conversion.")
        return images
    except Exception as e:
        messagebox.showerror("Error", f"Failed to convert PDF to image: {e}")
        return []

# Function to extract text using OCR
def extract_text_with_ocr(pdf_path):
    images = pdf_to_image(pdf_path)
    if not images:
        return ""
    reader = easyocr.Reader(['en'], gpu=False)
    ocr_text = ""
    for img in images:
        ocr_text += " ".join(text for _, text, _ in reader.readtext(np.array(img)))
    return ocr_text.strip()

# Function to process text for speech
def process_text_for_speech(text):
    text = re.sub(r'([.?!])', r'\1 ', text)
    return text

# Function to convert text to speech
def text_to_speech_with_expressions(text, output_path):
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    volume = engine.getProperty('volume')
    engine.setProperty('volume', 1)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    processed_text = process_text_for_speech(text)
    if isinstance(processed_text, str):
        engine.save_to_file(processed_text, output_path)
        engine.runAndWait()
    else:
        messagebox.showerror("Error", "Processed text is not a valid string")

# Function to convert entire text to audiobook
def convert_to_audiobook(full_text, audiobook_path, progress_var, spinner_label):
    try:
        spinner_label.config(text="Generating audiobook...")
        progress_var.set(0)
        os.makedirs("audiobooks", exist_ok=True)
        text_to_speech_with_expressions(full_text, audiobook_path)
        progress_var.set(100)
        spinner_label.config(text="Audiobook generated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate audiobook: {e}")

# Function to play the generated audiobook
def play_audiobook(audiobook_path):
    if os.path.exists(audiobook_path):
        playsound(audiobook_path)
    else:
        messagebox.showerror("Error", "Audiobook not found! Please generate the audiobook first.")

# Function to check if file already exists and append number if needed
def get_unique_filename(base_path):
    base, ext = os.path.splitext(base_path)
    counter = 1
    while os.path.exists(base + f"_{counter}" + ext):
        counter += 1
    return base + f"_{counter}" + ext

# Function to handle file upload and processing
def upload_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not file_path:
        messagebox.showerror("Error", "No file selected!")
        return

    def process_pdf():
        try:
            spinner_label.config(text="Extracting text...")
            extracted_text = extract_text_from_pdf(file_path)

            if not extracted_text:
                spinner_label.config(text="PDF text extraction failed. Trying OCR...")
                extracted_text = extract_text_with_ocr(file_path)

            if not extracted_text:
                spinner_label.config(text="No text extracted.")
                return

            filename = os.path.basename(file_path)
            global audiobook_path
            audiobook_filename = os.path.splitext(filename)[0] + ".mp3"
            audiobook_path = os.path.join("audiobooks", audiobook_filename)
            audiobook_path = get_unique_filename(audiobook_path)

            threading.Thread(target=convert_to_audiobook,
                             args=(extracted_text, audiobook_path, progress_var, spinner_label)).start()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    threading.Thread(target=process_pdf).start()

# Main Window
window = tk.Tk()
window.title("PDF to Audiobook Converter")
window.geometry("1280x720")
window.configure(bg="#1E1E1E")

# Header Section
header_frame = tk.Frame(window, bg="#42A5F5", height=100)
header_frame.pack(fill="x")

header_label = tk.Label(header_frame, text="PDF to Audiobook Converter", font=("Helvetica", 30, "bold"),
                        bg="#42A5F5", fg="white")
header_label.pack(pady=30)

# Main Frame
main_frame = tk.Frame(window, bg="#1E1E1E")
main_frame.pack(expand=True, fill="both", padx=60, pady=60)

# Upload Button
upload_button = tk.Button(main_frame, text="Upload PDF", command=upload_pdf, font=("Helvetica", 16, "bold"),
                          bg="#FF4081", fg="white", height=2, width=25, relief="flat", activebackground="#F50057",
                          activeforeground="white")
upload_button.pack(pady=20)

# Progress Bar
progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100, length=600, mode='determinate')
progress_bar.pack(pady=20)

# Spinner Label
spinner_label = tk.Label(main_frame, text="", font=("Helvetica", 14), bg="#1E1E1E", fg="white")
spinner_label.pack(pady=10)

# Play Audiobook Button
play_button = tk.Button(main_frame, text="Play Audiobook", font=("Helvetica", 16, "bold"), bg="#66BB6A", fg="white",
                        height=2, width=25, relief="flat", activebackground="#388E3C", activeforeground="white",
                        command=lambda: play_audiobook(audiobook_path))
play_button.pack(pady=20)

# Exit Button
exit_button = tk.Button(main_frame, text="Exit", font=("Helvetica", 16, "bold"), bg="#EF5350", fg="white", height=2,
                        width=25, relief="flat", activebackground="#D32F2F", activeforeground="white", command=window.quit)
exit_button.pack(pady=20)

# Footer Section
footer_frame = tk.Frame(window, bg="#42A5F5", height=50)
footer_frame.pack(fill="x", side="bottom")

footer_label = tk.Label(footer_frame, text="Powered by AI | PDF to Audiobook | 2024", font=("Helvetica", 12),
                        bg="#42A5F5", fg="white")
footer_label.pack()

# Run the Tkinter application
window.mainloop()
