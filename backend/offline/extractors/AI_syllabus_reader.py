from google import genai
from google.genai import types
import time
import json
import os

# 1. Set up your API Key
api_key = input("Enter your API Key: ")
client = genai.Client(api_key=api_key)


def process_syllabus_with_ai(pdf_path):
    print(f"Uploading {pdf_path} to Gemini... (This may take a minute for a 300+ page PDF)")

    # 2. Upload the file to the Gemini API
    pdf_file = client.files.upload(file=pdf_path, config=types.UploadFileConfig(display_name="ESAT Physics Syllabus"))

    # PDFs require a brief moment to be processed by Google's servers
    print("Waiting for Google's servers to process the document...")
    while pdf_file.state == types.FileState.PROCESSING:
        time.sleep(5)
        pdf_file = client.files.get(name=pdf_file.name)

    if pdf_file.state == types.FileState.FAILED:
        raise ValueError("Document processing failed.")

    print("Document ready! Sending extraction instructions...")

    # 4. Craft the strict prompt to get exactly what we need
    prompt = """
    You are an expert data extraction assistant. I have uploaded the Exam Guide.

    Your task is to extract the syllabus specification guidelines.
    Throughout the document, there are chapters like P1.Electricity(shown on a single page with only the chapter name) and sub-chapters with IDs like P1.1, P1.2, P2.1, etc. or any similar titles.
    Under each ID, there is a title (e.g., "Electrostatics") and a list of objectives (e.g., "a. Know and understand...").

    Please extract EVERY sub-chapter ID, its corresponding Chapter name, its Title, and its Objectives.
    Every sub-chapter MUST have 4 fields: id, chapter, title, objectives.
    CRITICAL INSTRUCTIONS:
    1. If there are math equations, symbols, or variables, convert them into standard LaTeX format (e.g., $E=mc^2$).
    2. Output the result STRICTLY as a JSON array of objects. Do not include any conversational text.
    3. Use the following JSON format:
    [
        {
            "id": "P1.1",
            "chapter":"P1.Electricity",
            "title": "Electrostatics",
            "objectives": "a: Know and understand that insulators... 
                            b: Know that charging..."
        }
    ]
    """

    # 5. Generate the response
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[pdf_file, prompt],
        config=types.GenerateContentConfig(max_output_tokens=100000)
    )

    # Clean up the output (sometimes the AI wraps JSON in markdown block quotes like ```json ... ```)
    raw_text = response.text
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("```json").strip("```")

    return raw_text


# ==========================================
# Run the Extraction
# ==========================================
if __name__ == "__main__":
    pdf_path = r"d:\Python Projects\PaperSplitter2.0\ExperiData\ESAT_Guide_Physics_June2025.pdf"
    output_json_path = "structured_syllabus_physics.json"

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
