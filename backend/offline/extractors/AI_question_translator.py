import google.generativeai as genai
import time
import json

# Insert your valid API key here
YOUR_ACTUAL_KEY = input("Enter your API KEY:")
genai.configure(api_key=YOUR_ACTUAL_KEY)

def process_and_classify_exam(pdf_path, syllabus_path):
    # 1. Load your Syllabus JSON as a string so Gemini can read it
    print("Loading Syllabus...")
    with open(syllabus_path, 'r', encoding='utf-8') as f:
        syllabus_content = f.read()

    print(f"Uploading {pdf_path} to Gemini...")
    pdf_file = genai.upload_file(path=pdf_path, display_name="Physics Past Paper")
    
    while pdf_file.state.name == "PROCESSING":
        time.sleep(5)
        pdf_file = genai.get_file(pdf_file.name)
        
    print("Document ready! Extracting and Classifying...")

    model = genai.GenerativeModel('gemini-2.5-flash')

    # 2. The Mega-Prompt: We combine extraction and classification
    # 2. The Ultra-Fast Classification Prompt
    prompt = f"""
    You are an expert Physics and Math teacher and examiner. 
    I have uploaded a Physics and Math past paper.
    
    Here is our official Syllabus in JSON format:
    {syllabus_content}
    
    YOUR TASK:
    Read every single question in the uploaded exam paper. For each question, compare its underlying physics and math concepts to the Syllabus, and assign the single best Sub-Chapter ID (topic_id).
    
    CRITICAL INSTRUCTIONS:
    1. DO NOT transcribe the question text.
    2. DO NOT extract options or write image descriptions.
    3. ONLY output the question number and the matching topic_id.
    4. If a question covers multiple topics, pick the primary one.
    
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

    # We can increase the output token limit just in case it's a long exam!
    generation_config = genai.GenerationConfig(max_output_tokens=8192)

    response = model.generate_content(
        [pdf_file, prompt], 
        generation_config=generation_config
    )
    
    raw_text = response.text
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("```json").strip("```")
        
    return raw_text

# ==========================================
# Run it
# ==========================================
if __name__ == "__main__":
    pdf_path = r"D:\PycharmProjects\PaperSplitter2.0\ExperiData\ENGAA_2016_S1_QuestionPaper.pdf"
    syllabus_path = "structured_syllabus_math.json" # Point this to your syllabus file
    output_json_path = "classified_questions_math.json"
    
    try:
        json_data = process_and_classify_exam(pdf_path, syllabus_path)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        print("Success! Questions extracted and classified.")
    except Exception as e:
        print(f"Error: {e}")