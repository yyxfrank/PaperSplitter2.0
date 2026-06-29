from google import genai
from google.genai import types
import time
import json

# 1. Set up your API Key
YOUR_ACTUAL_KEY = input("Enter your API KEY:")
client = genai.Client(api_key=YOUR_ACTUAL_KEY)

def process_and_classify_exam(pdf_path, syllabus_path):
    # 1. Load your Syllabus JSON as a string so Gemini can read it
    print("Loading Syllabus...")
    with open(syllabus_path, 'r', encoding='utf-8') as f:
        syllabus_content = f.read()

    print(f"Uploading {pdf_path} to Gemini...")

    # 2. Upload the file to the Gemini API
    pdf_file = client.files.upload(file=pdf_path, config=types.UploadFileConfig(display_name="Physics Past Paper"))

    # PDFs require a brief moment to be processed by Google's servers
    print("Waiting for Google's servers to process the document...")
    while pdf_file.state == types.FileState.PROCESSING:
        time.sleep(5)
        pdf_file = client.files.get(name=pdf_file.name)

    if pdf_file.state == types.FileState.FAILED:
        raise ValueError("Document processing failed.")

    print("Document ready! Extracting and Classifying...")

    # 3. The Ultra-Fast Classification Prompt
    prompt = f"""
    You are an expert Physics teacher and examiner.
    I have uploaded a Physics past paper.

    Here is our official Syllabus in JSON format:
    {syllabus_content}

    YOUR TASK:
    Read every single question in the uploaded exam paper. For each question, compare its underlying physics concepts to the Syllabus, and assign the single best Sub-Chapter ID (topic_id).

    CRITICAL INSTRUCTIONS:
    1. DO NOT transcribe the question text.
    2. DO NOT extract options or write image descriptions.
    3. ONLY output the question number and the matching topic_id.
    4. If a question covers multiple topics, pick the primary one.
    5. If a question has more to do with math than physics, skip it and move on to the next question.
    Output STRICTLY as a JSON array of objects.

    Use the following exact JSON format:
    [
        {{
            "question_number": 1,
            "topic_id": "P1.1"
        }},
        {{
            "question_number": 2,
            "topic_id": "P3.4"
        }}
    ]
    """

    # 4. Generate the response
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[pdf_file, prompt],
        config=types.GenerateContentConfig(max_output_tokens=8192)
    )

    raw_text = response.text
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("```json").strip("```")

    return raw_text


# ==========================================
# Run it
# ==========================================
if __name__ == "__main__":
    pdf_path = r"d:\Python Projects\PaperSplitter2.0\ExperiData\ENGAA_2016_S1_QuestionPaper.pdf"
    syllabus_path = "structured_syllabus_physics.json"  # Point this to your syllabus file
    output_json_path = "classified_questions_physics.json"

    try:
        json_data = process_and_classify_exam(pdf_path, syllabus_path)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        print("Success! Questions extracted and classified.")
    except Exception as e:
        print(f"Error: {e}")
