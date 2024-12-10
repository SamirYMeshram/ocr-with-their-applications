import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, simpledialog
from PIL import Image, ImageTk
import easyocr
import cv2
import numpy as np
import threading
from googletrans import Translator
from concurrent.futures import ThreadPoolExecutor
from fuzzywuzzy import fuzz

# Configure Gemini API Key
genai.configure(api_key="AIzaSyAAJ15nQvTb4HjwPcfxHT1F_LWgFSgdWxc")

# Global variables
executor = ThreadPoolExecutor(max_workers=3)

def preprocess_image(image_path):
    """
    Enhance image clarity for OCR.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found or invalid.")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        return cleaned
    except Exception as e:
        messagebox.showerror("Error", f"Image preprocessing failed: {e}")
        return None

def easyocr_text_detection(image_path):
    """
    Perform OCR with EasyOCR and return bounding box data.
    """
    try:
        img = preprocess_image(image_path)
        if img is None:
            return None, [], ""

        # Initialize EasyOCR reader
        reader = easyocr.Reader(['en'], gpu=True)  # Ensure the correct instantiation
        detections = reader.readtext(img)

        annotated_img = cv2.imread(image_path)
        extracted_text = ""
        prev_right = 0
        bbox_list = []

        for bbox, text, score in detections:
            if score > 0.3:
                top_left = tuple(map(int, bbox[0]))
                bottom_right = tuple(map(int, bbox[2]))
                bbox_list.append((top_left, bottom_right, text))

                # Calculate space heuristic
                if top_left[0] - prev_right > 20:  # Gap between boxes
                    extracted_text += " "
                extracted_text += text
                prev_right = bottom_right[0]

        return annotated_img, bbox_list, extracted_text
    except Exception as e:
        messagebox.showerror("Error", f"EasyOCR failed: {e}")
        return None, [], ""

def gemini_refine_text(extracted_text):
    """
    Use Gemini AI to refine OCR output for spaces, grammar, and readability.
    """
    prompt = (
        "Please refine the following text extracted from an image. "
        "Correct any spacing, grammatical errors, and make it readable:\n\n"
    )
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content([prompt + extracted_text])
        return response.text.strip()
    except Exception as e:
        return f"Gemini AI analysis failed: {e}"

def translate_text(text, target_language="fr"):
    """
    Translate text using Google Translate API.
    """
    translator = Translator()
    try:
        translated = translator.translate(text, dest=target_language).text
        return translated
    except Exception as e:
        return f"Translation failed: {e}"

def ask_for_language():
    """
    Ask the user to select a target language for translation.
    """
    language_code = simpledialog.askstring("Select Language",
        "Enter the language code (e.g., 'es' for Spanish, 'fr' for French):")
    if language_code:
        return language_code
    return "en"  # Default to English

def fuzzy_match_word(original_word, refined_word):
    """
    Use fuzzy matching to compare the OCR word with the refined text.
    Return a similarity score.
    """
    return fuzz.ratio(original_word.lower(), refined_word.lower())

def process_image(image_path, result_window):
    """
    Complete pipeline: OCR detection and AI-based refinement inside the result window.
    """
    annotated_img, bbox_list, extracted_text = easyocr_text_detection(image_path)
    if not extracted_text.strip():
        messagebox.showwarning("No Text", "No text detected in the image.")
        return

    # Ask for translation language
    target_language = ask_for_language()

    # Gemini AI refinement and translation in a separate thread
    def refine_and_display():
        refined_text = gemini_refine_text(extracted_text)
        translated_extracted_text = translate_text(extracted_text, target_language)
        translated_refined_text = translate_text(refined_text, target_language)

        display_results(annotated_img, bbox_list, refined_text, translated_extracted_text, translated_refined_text, result_window)

    threading.Thread(target=refine_and_display, daemon=True).start()

def overlay_refined_text_on_image(annotated_img, bbox_list, extracted_text, refined_text):
    """
    Overlay the refined text from Gemini AI on the annotated image by matching each bounding box
    with the corresponding word from the refined text.
    """
    original_words = extracted_text.split()
    refined_words = refined_text.split()

    word_idx = 0
    for (top_left, bottom_right, original_word) in bbox_list:
        if word_idx < len(refined_words):
            # Match the OCR word to the refined word using fuzzy matching
            best_match = None
            best_score = 0

            for refined_word_candidate in refined_words:
                score = fuzzy_match_word(original_word, refined_word_candidate)
                if score > best_score:
                    best_score = score
                    best_match = refined_word_candidate

            # Overlay the best matching refined word onto the image
            cv2.putText(annotated_img, best_match, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            word_idx += 1

    return annotated_img

def display_results(annotated_img, bbox_list, refined_text, translated_ocr, translated_refined, result_window):
    """
    Display annotated image, refined text, and translations in the result window.
    """
    # Create canvas for scrollable results
    canvas = tk.Canvas(result_window)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(result_window, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

    result_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=result_frame, anchor="nw")

    # Overlay Gemini AI refined text onto image
    img_with_refined_text = overlay_refined_text_on_image(annotated_img, bbox_list, refined_text, refined_text)

    # Annotated image with refined text
    img = Image.fromarray(cv2.cvtColor(img_with_refined_text, cv2.COLOR_BGR2RGB))
    img_tk = ImageTk.PhotoImage(img)
    img_label = tk.Label(result_frame, image=img_tk)
    img_label.image = img_tk
    img_label.pack(pady=10)

    # Refined text
    tk.Label(result_frame, text="Gemini AI Refined Text:", font=("Helvetica", 14, "bold")).pack(pady=5)
    refined_textbox = tk.Text(result_frame, wrap="word", font=("Helvetica", 12))
    refined_textbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    refined_textbox.insert(tk.END, refined_text)
    refined_textbox.config(state=tk.DISABLED)

    # Translated OCR text
    tk.Label(result_frame, text="Translated OCR Text:", font=("Helvetica", 14, "bold")).pack(pady=5)
    translated_ocr_textbox = tk.Text(result_frame, wrap="word", font=("Helvetica", 12))
    translated_ocr_textbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    translated_ocr_textbox.insert(tk.END, translated_ocr)
    translated_ocr_textbox.config(state=tk.DISABLED)

    # Translated Refined text
    tk.Label(result_frame, text="Translated Refined Text:", font=("Helvetica", 14, "bold")).pack(pady=5)
    translated_refined_textbox = tk.Text(result_frame, wrap="word", font=("Helvetica", 12))
    translated_refined_textbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    translated_refined_textbox.insert(tk.END, translated_refined)
    translated_refined_textbox.config(state=tk.DISABLED)

    # Update scroll region after adding content
    result_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

def select_image_and_process():
    """
    Open file dialog to select an image and process it within a new window.
    """
    image_path = filedialog.askopenfilename(
        title="Select Image", filetypes=[("Image Files", ".jpg;.jpeg;*.png")]
    )
    if image_path:
        result_window = Toplevel(root)
        result_window.title("Processing Results")
        result_window.geometry("1000x800")
        process_image(image_path, result_window)

# GUI setup
root = tk.Tk()
root.title("Enhanced OCR + Gemini AI")
root.geometry("800x600")
root.configure(bg="#f4f4f9")

tk.Label(root, text="Enhanced OCR + Gemini AI", font=("Helvetica", 24, "bold"), bg="#4c8bf5", fg="white").pack(pady=20)
tk.Label(root, text="Select an image to analyze text with OCR and refine using Gemini AI.", font=("Helvetica", 14), bg="#f4f4f9").pack(pady=10)

# Button to trigger the new window for processing
tk.Button(root, text="Select Image and Process", font=("Helvetica", 16), bg="#3e64ff", fg="white", command=select_image_and_process).pack(pady=20)

root.mainloop()
