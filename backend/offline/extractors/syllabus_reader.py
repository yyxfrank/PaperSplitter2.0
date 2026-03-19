import pdfplumber

def extract_syllabus_text(pdf_path):
    """
    Extracts and returns all text from a given PDF file.
    """
    print(f"Processing: {pdf_path}...\n")
    full_text = ""
    
    # Safely open the PDF
    with pdfplumber.open(pdf_path) as pdf:
        
        # Loop through every page in the document
        for i, page in enumerate(pdf.pages):
            
            # Extract the text from the current page
            page_text = page.extract_text()
            
            # Check if text was actually found (scanned images might return None)
            if page_text:
                full_text += f"\n--- Page {i + 1} ---\n"
                full_text += page_text
            else:
                print(f"Warning: No extractable text found on page {i + 1}.")
                
    return full_text

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # Replace with the actual path to your syllabus PDF
    pdf_file_path = "ExperiData/ESAT_Guide_Physics_June2025.pdf" 
    
    try:
        extracted_data = extract_syllabus_text(pdf_file_path)
        
        # Print the first 1000 characters just to verify it worked
        print("Extraction Successful! Here is a preview:\n")
        print(extracted_data[:1000]) 
        
    except FileNotFoundError:
        print(f"Error: Could not find the file at {pdf_file_path}. Please check the path.")