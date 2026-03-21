import google.generativeai as genai
import time
import json

# Insert your valid API key here
YOUR_ACTUAL_KEY = input("Enter your API KEY:")
genai.configure(api_key=YOUR_ACTUAL_KEY)

def process_exam_paper(pdf_path):
    print(f"Uploading {pdf_path} to Gemini...")
    
    pdf_file = genai.upload_file(path=pdf_path, display_name="Physics Past Paper")
    
    print("Waiting for Google's servers to process the document...")
    while pdf_file.state.name == "PROCESSING":
        time.sleep(5)
        pdf_file = genai.get_file(pdf_file.name)
        
    if pdf_file.state.name == "FAILED":
        raise ValueError("Document processing failed.")
        
    print("Document ready! Slicing questions...")

    model = genai.GenerativeModel('gemini-2.5-flash')

    # THE NEW PROMPT: Tailored for Exam Papers with Images
    prompt = """
    You are an expert exam parser. I have uploaded a Physics past paper.
    Your task is to extract every single question from this exam paper.
    
    CRITICAL INSTRUCTIONS:
    1. Extract the question number and the full text of the question.
    2. EQUATIONS: Convert all math, variables, and equations into LaTeX format (e.g., $v = u + at$).
    3. OPTIONS: If it is a multiple-choice question, extract the options into an array. If not, leave the array empty.
    4. IMAGES/DIAGRAMS: If the question contains an image, graph, or diagram, you MUST write a detailed text description of it. For example: "A circuit diagram showing a 9V battery connected in parallel with two 10 ohm resistors." This is vital for our topic-matching algorithm. If there is no image, write "None".
    5. Output STRICTLY as a JSON array of objects. Do not include any conversational text.
    
    Use the following JSON format:
    [
        {
            "question_number": "1",
            "text": "A car accelerates uniformly from rest at $2.5 m/s^2$. What is its velocity after 4 seconds?",
            "options": ["A. 5 m/s", "B. 10 m/s", "C. 15 m/s", "D. 20 m/s"],
            "image_description": "None"
        },
        {
            "question_number": "2",
            "text": "Calculate the total resistance in the circuit shown below.",
            "options": [],
            "image_description": "A circuit diagram containing a 12V DC power supply connected in series with a 4 ohm resistor and a parallel combination of two 6 ohm resistors."
        }
    ]
    """

    response = model.generate_content([pdf_file, prompt])
    
    raw_text = response.text
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("```json").strip("```")
        
    return raw_text

if __name__ == "__main__":
    # Point this to your past paper PDF
    pdf_path = r"D:\PycharmProjects\PaperSplitter2.0\ExperiData\Sample_Past_Paper.pdf"
    output_json_path = "sliced_questions.json"
    
    try:
        json_data = process_exam_paper(pdf_path)
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
            
        print(f"\nSuccess! The sliced questions have been saved to '{output_json_path}'.")
        
    except Exception as e:
        print(f"An error occurred: {e}")