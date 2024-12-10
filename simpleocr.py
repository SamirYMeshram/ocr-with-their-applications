import google.generativeai as genai
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from googletrans import Translator
import pyttsx3
import threading

# Configure the API key directly
genai.configure(api_key="AIzaSyAAJ15nQvTb4HjwPcfxHT1F_LWgFSgdWxc")

# Initialize the Google Translator
translator = Translator()

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Language mapping from code to name
language_names = {
    "af": "Afrikaans", "sq": "Albanian", "ar": "Arabic", "hy": "Armenian", "bn": "Bengali", "bs": "Bosnian",
    "ca": "Catalan", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch", "en": "English",
    "eo": "Esperanto", "et": "Estonian", "tl": "Filipino", "fi": "Finnish", "fr": "French", "de": "German",
    "el": "Greek", "gu": "Gujarati", "hi": "Hindi", "hu": "Hungarian", "is": "Icelandic", "id": "Indonesian",
    "it": "Italian", "ja": "Japanese", "jw": "Javanese", "ka": "Georgian", "km": "Khmer", "ko": "Korean",
    "la": "Latin", "lv": "Latvian", "lt": "Lithuanian", "ml": "Malayalam", "mr": "Marathi", "my": "Myanmar",
    "ne": "Nepali", "no": "Norwegian", "pl": "Polish", "pt": "Portuguese", "ro": "Romanian", "ru": "Russian",
    "sr": "Serbian", "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian", "es": "Spanish", "su": "Sundanese",
    "sw": "Swahili", "sv": "Swedish", "ta": "Tamil", "te": "Telugu", "th": "Thai", "tr": "Turkish", "uk": "Ukrainian",
    "ur": "Urdu", "vi": "Vietnamese", "cy": "Welsh", "zu": "Zulu"
}

languages = ["Select Language"] + list(language_names.values())


def prep_image(image_path):
    try:
        sample_file = genai.upload_file(path=image_path, display_name="Uploaded Image")
        return sample_file
    except Exception as e:
        messagebox.showerror("Error", f"Failed to upload image: {e}")
        return None


def extract_text_from_image(image_path, prompt):
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content([image_path, prompt])
        return response.text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process image: {e}")
        return None


def handle_process_image(prompt):
    image_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=(("Image Files", "*.jpg;*.jpeg;*.png"), ("All Files", "*.*"))
    )

    if not image_path:
        return

    display_image(image_path)

    sample_file = prep_image(image_path)
    if sample_file:
        result = extract_text_from_image(sample_file, prompt)
        if result:
            result_textbox.delete("1.0", tk.END)
            result_textbox.insert(tk.END, result)
        else:
            result_textbox.delete("1.0", tk.END)
            result_textbox.insert(tk.END, "No result or analysis failed.")

    # Update scrollable region after result is inserted
    update_scroll_region()


def display_image(image_path):
    img = Image.open(image_path)

    window_width = root.winfo_width() * 0.8
    window_height = root.winfo_height() * 0.5

    img.thumbnail((window_width, window_height))
    img_tk = ImageTk.PhotoImage(img)

    image_label.config(image=img_tk)
    image_label.image = img_tk

    image_label.grid(row=1, column=0, columnspan=2, pady=20)
    update_scroll_region()


def translate_text():
    extracted_text = result_textbox.get("1.0", tk.END).strip()
    if not extracted_text:
        messagebox.showwarning("No Text", "Please extract text first.")
        return

    target_language = language_var.get()
    if target_language == "Select Language":
        messagebox.showwarning("No Language", "Please select a language to translate.")
        return

    target_language_code = [code for code, name in language_names.items() if name == target_language][0]
    translated = translator.translate(extracted_text, dest=target_language_code)
    result_textbox.delete("1.0", tk.END)
    result_textbox.insert(tk.END, translated.text)

    update_scroll_region()


def save_results_to_file():
    extracted_text = result_textbox.get("1.0", tk.END).strip()
    if not extracted_text:
        messagebox.showwarning("No Text", "No analysis results to save.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, 'w') as file:
            file.write(extracted_text)
        messagebox.showinfo("Saved", f"Results saved to {file_path}")


def speak_result():
    global is_speaking
    extracted_text = result_textbox.get("1.0", tk.END).strip()

    if not extracted_text:
        messagebox.showwarning("No Text", "Please extract text first.")
        return

    if is_speaking:
        engine.stop()
        speak_button.config(text="Speak Result")
        is_speaking = False
    else:
        def speak_async():
            engine.say(extracted_text)
            engine.runAndWait()

        threading.Thread(target=speak_async, daemon=True).start()
        speak_button.config(text="Stop Speaking")
        is_speaking = True


def update_scroll_region():
    scrollable_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


root = tk.Tk()
root.title("Gemini AI Image Analyzer")
root.state('zoomed')
root.configure(bg="#f0f4f8")

canvas = tk.Canvas(root, bg="#f0f4f8")
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#f0f4f8")

canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(fill="both", expand=True)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

main_frame = tk.Frame(scrollable_frame, bg="#ffffff", padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

title_frame = tk.Frame(main_frame, bg="#5a67d8", bd=0)
title_frame.grid(row=0, column=0, columnspan=2, pady=20)

title_label = tk.Label(
    title_frame,
    text="Gemini AI Image Analyzer",
    font=("Helvetica", 32, "bold"),
    bg="#5a67d8",
    fg="white",
    padx=20,
    pady=20,
)
title_label.pack()

image_label = tk.Label(main_frame, text="No Image Selected", bg="#d9d9d9", relief="solid")
image_label.grid(row=1, column=0, columnspan=2, pady=20)

language_label = tk.Label(main_frame, text="Select Target Language for Translation:", font=("Helvetica", 14), bg="#f0f4f8")
language_label.grid(row=2, column=0, pady=10, sticky="w")

language_var = tk.StringVar()
language_var.set(languages[0])

language_menu = tk.OptionMenu(main_frame, language_var, *languages)
language_menu.config(font=("Helvetica", 14), width=20)
language_menu.grid(row=2, column=1, pady=10)

translate_button = tk.Button(
    main_frame,
    text="Translate Text",
    font=("Helvetica", 16),
    bg="#48bb78",
    fg="white",
    padx=20,
    pady=10,
    command=translate_text,
)
translate_button.grid(row=3, column=0, columnspan=2, pady=20)

new_image_button = tk.Button(
    main_frame,
    text="Choose New Image",
    font=("Helvetica", 16),
    bg="#48bb78",
    fg="white",
    padx=20,
    pady=10,
    command=lambda: handle_process_image("Extract the text in the image verbatim"),
)
new_image_button.grid(row=4, column=0, columnspan=2, pady=20)

speak_button = tk.Button(
    main_frame,
    text="Speak Result",
    font=("Helvetica", 16),
    bg="#48bb78",
    fg="white",
    padx=20,
    pady=10,
    command=speak_result,
)
speak_button.grid(row=5, column=0, columnspan=2, pady=20)

result_label = tk.Label(main_frame, text="Analysis Results", font=("Helvetica", 18, "bold"), bg="#f0f4f8", fg="#333")
result_label.grid(row=6, column=0, pady=10, columnspan=2)

result_textbox = tk.Text(main_frame, width=100, height=12, wrap="word", font=("Helvetica", 14), relief="solid",
                         borderwidth=1)
result_textbox.grid(row=7, column=0, columnspan=2, pady=10)

save_button = tk.Button(
    main_frame,
    text="Save Results",
    font=("Helvetica", 16),
    bg="#48bb78",
    fg="white",
    padx=20,
    pady=10,
    command=save_results_to_file,
)
save_button.grid(row=8, column=0, columnspan=2, pady=20)

footer_label = tk.Label(
    root,
    text="Powered by Gemini AI | Developed by You",
    font=("Helvetica", 12, "italic"),
    bg="#5a67d8",
    fg="white",
    pady=10,
)
footer_label.pack(side=tk.BOTTOM, fill=tk.X)

update_scroll_region()

root.mainloop()
