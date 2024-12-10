import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import fitz  # PyMuPDF for PDF manipulation
from googletrans import Translator
import os
import time
import random
import subprocess
import requests
from requests.exceptions import RequestException

# Function to upload a PDF file
def upload_pdf():
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_path = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF files", "*.pdf")])
    return file_path

# Function to extract text and fonts from PDF (including bounding box data)
def extract_text_and_fonts(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("dict")  # Extract detailed text data (including position, font, and size)

        page_data = []
        for block in text["blocks"]:
            for line in block["lines"]:
                for span in line["spans"]:
                    page_data.append({
                        "text": span["text"],
                        "font": span["font"],
                        "size": span["size"],
                        "bbox": span["bbox"]
                    })
        text_data.append(page_data)

    return text_data

# Function to split the text into chunks of approximately 100 words
def split_text_into_chunks(text, words_per_chunk=100):
    words = text.split()
    chunks = [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
    return chunks

# Function to translate chunks using Google Translate
def translate_chunks(chunks, target_language):
    translator = Translator()
    translated_chunks = []

    for i, chunk in enumerate(chunks):
        print(f"Translating chunk {i + 1} of {len(chunks)}...")
        retries = 3
        while retries > 0:
            try:
                translated_chunk = translator.translate(chunk, dest=target_language).text
                translated_chunks.append(translated_chunk)
                time.sleep(0.1)  # Add slight delay between requests to avoid rate limiting
                break
            except RequestException as e:
                print(f"Error during translation: {e}")
                retries -= 1
                if retries == 0:
                    print(f"Failed to translate chunk {i + 1}. Using original text.")
                    translated_chunks.append(chunk)
                    break
                print(f"Retrying... ({3 - retries} retries left)")
                time.sleep(random.randint(1, 3))  # Wait for a random time before retrying
    return translated_chunks

# Function to reconstruct the translated text and put it in the original layout
def reconstruct_text(original_data, translated_chunks):
    reconstructed_data = []
    translated_idx = 0
    chunk_idx = 0

    for page_data in original_data:
        page_reconstructed = []

        for data in page_data:
            if chunk_idx < len(translated_chunks):
                translated_word = translated_chunks[chunk_idx]
                chunk_idx += 1
            else:
                translated_word = data["text"]

            page_reconstructed.append({
                "text": translated_word,
                "font": data["font"],
                "size": data["size"],
                "bbox": data["bbox"]
            })

        reconstructed_data.append(page_reconstructed)

    return reconstructed_data

# Function to extract images from the PDF
def extract_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            images.append((page_num, image_bytes, img[1]))  # Include image information

    return images

# Function to generate a new PDF with translated text and original images
def generate_pdf_with_translated_text(original_data, images, output_path):
    doc = fitz.open()  # Create a new PDF document

    image_idx = 0
    for page_data in original_data:
        page = doc.new_page()  # Create a new page in the PDF

        # Insert the translated text
        for data in page_data:
            try:
                page.insert_text(
                    (data["bbox"][0], data["bbox"][1]),
                    data["text"],
                    fontsize=data["size"],
                    fontname="helv"  # Use a default font if original font is unavailable
                )
            except Exception as e:
                print(f"Error inserting text: {e}")

        # Insert images
        while image_idx < len(images) and images[image_idx][0] == len(doc) - 1:
            _, image_data, img_info = images[image_idx]
            image_file = f"temp_image_{image_idx}.png"
            with open(image_file, "wb") as f:
                f.write(image_data)
            page.insert_image((img_info[0], img_info[1], img_info[2], img_info[3]), filename=image_file)
            os.remove(image_file)
            image_idx += 1

    doc.save(output_path)

# Main program
def main():
    print("Starting the PDF translation process...")

    # Upload the PDF
    pdf_file = upload_pdf()
    if not pdf_file:
        print("No PDF selected, exiting...")
        return

    # Extract text and font details
    original_data = extract_text_and_fonts(pdf_file)
    if not original_data:
        print("Error extracting text from PDF.")
        return

    # Ask user for the target language
    target_lang = simpledialog.askstring("Input", "Enter the target language code (e.g., 'es' for Spanish):")
    if not target_lang:
        print("No target language provided, exiting...")
        return

    # Combine all text for translation
    full_text = " ".join([data["text"] for page in original_data for data in page])

    # Split text into chunks and translate
    chunks = split_text_into_chunks(full_text, words_per_chunk=100)
    translated_chunks = translate_chunks(chunks, target_lang)

    # Reconstruct text into the original PDF layout
    reconstructed_data = reconstruct_text(original_data, translated_chunks)

    # Extract images from the PDF
    images = extract_images(pdf_file)

    # Prepare output folder and file path
    output_folder = "PDFoutput"
    os.makedirs(output_folder, exist_ok=True)
    output_file_name = os.path.splitext(os.path.basename(pdf_file))[0] + "_translated.pdf"
    output_path = os.path.join(output_folder, output_file_name)

    # Generate the new PDF
    generate_pdf_with_translated_text(reconstructed_data, images, output_path)

    print(f"PDF generation complete! The translated PDF is saved as: {output_path}")
    messagebox.showinfo("Success", f"PDF generated successfully! File saved to: {output_path}")

    # Open the output PDF file
    subprocess.Popen([output_path], shell=True)

if __name__ == "__main__":
    main()
