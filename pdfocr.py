import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pdfplumber
from transformers import pipeline
import pyttsx3
import easyocr
import pdf2image
from pydub import AudioSegment
import random

# NLP Models
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    device=0
)

dialogue_identifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=0
)

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract text from PDF: {e}")
        return ""

def pdf_to_image(pdf_path):
    try:
        return pdf2image.convert_from_path(pdf_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to convert PDF to image: {e}")
        return []

def extract_text_with_ocr(pdf_path):
    images = pdf_to_image(pdf_path)
    if not images:
        return ""
    reader = easyocr.Reader(['en'], gpu=False)
    ocr_text = ""
    for img in images:
        ocr_text += " ".join(text for _, text, _ in reader.readtext(img))
    return ocr_text.strip()

def classify_text(full_text):
    sentences = [s.strip() for s in full_text.split(". ") if s.strip()]
    classified_text = {"narrative": [], "dialogue": []}
    results = dialogue_identifier(
        sentences,
        candidate_labels=["dialogue", "narrative"],
        truncation=True
    )
    for sentence, result in zip(sentences, results):
        label = result['labels'][0]
        classified_text[label].append(sentence)
    return classified_text

def analyze_sentiments(sentences):
    sentiments = sentiment_analyzer(sentences)
    return [(s['label'], s['score']) for s in sentiments]

def text_to_speech_dynamic(text, output_path, style="Neutral"):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        if style == "Fiction":
            engine.setProperty('rate', 150)
            engine.setProperty('voice', voices[0].id)
        elif style == "Non-fiction":
            engine.setProperty('rate', 170)
            engine.setProperty('voice', voices[1].id)
        elif style == "Poetry":
            engine.setProperty('rate', 120)
        elif style == "Textbooks":
            engine.setProperty('rate', 100)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to synthesize speech: {e}")

def convert_to_audiobook(full_text, audiobook_path, progress_var, spinner_label):
    try:
        if not full_text:
            raise ValueError("No text to process")
        spinner_label.config(text="Generating audiobook...")
        os.makedirs("audiobooks", exist_ok=True)
        classified_text = classify_text(full_text)
        combined_audio = AudioSegment.empty()
        for category, sentences in classified_text.items():
            sentiments = analyze_sentiments(sentences)
            for i, (sentence, (sentiment, score)) in enumerate(zip(sentences, sentiments)):
                style = "Neutral"
                if category == "dialogue":
                    style = "Fiction"
                style = "Poetry" if sentiment == "POSITIVE" and score > 0.9 else style
                temp_audio_path = f"temp_{random.randint(1000, 9999)}.mp3"
                text_to_speech_dynamic(sentence, temp_audio_path, style)
                if os.path.exists(temp_audio_path):
                    combined_audio += AudioSegment.from_file(temp_audio_path)
                    os.remove(temp_audio_path)
                else:
                    raise FileNotFoundError(f"Failed to generate audio for sentence: {sentence}")
                progress_var.set((i + 1) / len(sentences) * 100)
                spinner_label.update()
        combined_audio.export(audiobook_path, format="mp3")
        spinner_label.config(text="Audiobook generated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate audiobook: {e}")

def process_pdf(file_path, progress_var, spinner_label):
    spinner_label.config(text="Extracting text...")
    extracted_text = extract_text_from_pdf(file_path)
    ocr_text = extract_text_with_ocr(file_path)
    full_text = f"{extracted_text}\n{ocr_text}".strip()
    if not full_text:
        spinner_label.config(text="No text extracted.")
        return
    audiobook_path = os.path.join("audiobooks", "audiobook.mp3")
    threading.Thread(target=convert_to_audiobook, args=(full_text, audiobook_path, progress_var, spinner_label)).start()

def upload_pdf(progress_var, spinner_label):
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not file_path:
        messagebox.showerror("Error", "No file selected!")
        return
    threading.Thread(target=process_pdf, args=(file_path, progress_var, spinner_label)).start()

def main():
    window = tk.Tk()
    window.title("Advanced PDF to Audiobook Converter")
    window.geometry("500x300")
    upload_button = tk.Button(window, text="Upload PDF", command=lambda: upload_pdf(progress_var, spinner_label))
    upload_button.pack(pady=20)
    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(window, variable=progress_var, maximum=100)
    progress_bar.pack(pady=20, fill=tk.X)
    spinner_label = tk.Label(window, text="")
    spinner_label.pack()
    window.mainloop()

if __name__ == "__main__":
    main()
