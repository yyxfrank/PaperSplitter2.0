import google.generativeai as genai
import time
import json
import os

# 1. Set up your API Key
# Replace 'YOUR_API_KEY' with your actual key, or set it as an environment variable
api_KEY=input("Enter your API Key: ")
genai.configure(api_key=api_KEY)



def process_syllabus_with_ai(pdf_path):
    # api_key=input("Enter your API Key: ")
   
    print(f"Uploading {pdf_path} to Gemini... (This may take a minute for a 300+ page PDF)")
    
    # 2. Upload the file to the Gemini API
    pdf_file = genai.upload_file(path=pdf_path, display_name="ESAT Physics Syllabus")
    
    # PDFs require a brief moment to be processed by Google's servers
    print("Waiting for Google's servers to process the document...")
    while pdf_file.state.name == "PROCESSING":
        time.sleep(5)
        # Refresh the file status
        pdf_file = genai.get_file(pdf_file.name)
        
    if pdf_file.state.name == "FAILED":
        raise ValueError("Document processing failed.")
        
    print("Document ready! Sending extraction instructions...")

    # 3. Initialize the model (Gemini 1.5 Flash is incredibly fast and great for large documents)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 4. Craft the strict prompt to get exactly what we need
    prompt = """
    You are an expert data extraction assistant. I have uploaded the Exam Guide.
    
    Your task is to extract the syllabus specification guidelines. 
    Throughout the document, there are sub-chapters with IDs like P1.1, P1.2, P2.1, etc. or any similar titles.
    Under each ID, there is a title (e.g., "Electrostatics") and a list of objectives (e.g., "a. Know and understand...").
    
    Please extract EVERY sub-chapter ID, its Title, and its Objectives.
    
    CRITICAL INSTRUCTIONS:
    1. If there are math equations, symbols, or variables, convert them into standard LaTeX format (e.g., $E=mc^2$).
    2. Output the result STRICTLY as a JSON array of objects. Do not include any conversational text.
    3. Use the following JSON format:
    [
        {
            "id": "P1.1",
            "title": "Electrostatics",
            "objectives": "a. Know and understand that insulators... b. Know that charging..."
        }
    ]
    """

    # 5. Generate the response
    response = model.generate_content([pdf_file, prompt])
    
    # Clean up the output (sometimes the AI wraps JSON in markdown block quotes like ```json ... ```)
    raw_text = response.text
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("```json").strip("```")
        
    return raw_text

# ==========================================
# Run the Extraction
# ==========================================
if __name__ == "__main__":
    pdf_path = r"D:\PycharmProjects\PaperSplitter2.0\ExperiData\TMUA_Content_Specification_April2025.pdf"
    output_json_path = "structured_syllabus_math.json"
    
    try:
        # Extract the data
        json_data = process_syllabus_with_ai(pdf_path)
        
        # Save the data to a file
        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
            
        print(f"\nSuccess! The structured syllabus has been saved to '{output_json_path}'.")
        
        # Print a small preview
        parsed_json = json.loads(json_data)
        print(f"\nExtracted {len(parsed_json)} sub-chapters. Preview of the first one:")
        print(json.dumps(parsed_json[0], indent=4))
        
    except Exception as e:
        print(f"An error occurred: {e}")