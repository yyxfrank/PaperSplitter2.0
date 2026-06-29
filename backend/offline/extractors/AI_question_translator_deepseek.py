import os
import json
import re
import fitz  # PyMuPDF
from openai import OpenAI

# ==========================================
# DeepSeek Configuration
# ==========================================
DEEPSEEK_API_KEY = input("Enter your DeepSeek API Key: ")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a PDF file page by page using PyMuPDF.
    Used to feed exam content to DeepSeek (which does not natively process PDF files).
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        str: Concatenated text of all pages
    """
    print(f"Extracting text from {pdf_path}...")
    doc = fitz.open(pdf_path)
    full_text = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        full_text.append(f"--- Page {page_num + 1} ---\n{text}")
    
    doc.close()
    return "\n\n".join(full_text)


def process_and_classify_exam(pdf_path, syllabus_path):
    """
    Read a PDF exam paper, extract text, and use DeepSeek to classify
    each question to the best-matching Syllabus topic_id.
    
    Args:
        pdf_path: Path to the exam PDF
        syllabus_path: Path to the Syllabus JSON
        
    Returns:
        str: JSON string of classified questions
    """
    # 1. Load Syllabus
    print("Loading Syllabus...")
    with open(syllabus_path, "r", encoding="utf-8") as f:
        syllabus_content = f.read()

    # 2. Extract text from PDF
    exam_text = extract_text_from_pdf(pdf_path)

    # 3. Build the prompt
    prompt = f"""
You are an expert Physics teacher and examiner.
I have a Physics past paper (full text extracted below).

Here is our official Syllabus in JSON format:
{syllabus_content}

YOUR TASK:
Read every single question in the exam paper below. For each question, compare its underlying physics concepts to the Syllabus, and assign the single best Sub-Chapter ID (topic_id).

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

--- EXAM PAPER TEXT START ---
{exam_text}
--- EXAM PAPER TEXT END ---
"""

    # 4. Call DeepSeek API
    print(f"Sending to DeepSeek ({DEEPSEEK_MODEL}) for classification...")
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise exam classifier. You always output valid JSON arrays."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=8192,
        temperature=0.1
    )

    raw_text = response.choices[0].message.content

    # 5. Clean up markdown code block if present
    if raw_text.startswith("```"):
        # Remove ```json and ``` markers
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r"\s*```$", "", raw_text, flags=re.MULTILINE)

    return raw_text.strip()


# ==========================================
# Run it
# ==========================================
if __name__ == "__main__":
    pdf_path = r"D:\PycharmProjects\PaperSplitter2.0\ExperiData\ENGAA_2016_S1_QuestionPaper.pdf"
    syllabus_path = "structured_syllabus_math.json"
    output_json_path = "classified_questions_deepseek.json"

    try:
        json_data = process_and_classify_exam(pdf_path, syllabus_path)
        with open(output_json_path, "w", encoding="utf-8") as f:
            f.write(json_data)
        print(f"Success! Questions extracted and classified -> {output_json_path}")
    except Exception as e:
        print(f"Error: {e}")
