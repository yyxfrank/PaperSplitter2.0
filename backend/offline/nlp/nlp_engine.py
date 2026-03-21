from sentence_transformers import SentenceTransformer, util
import json

def match_question_to_chapter(question_file_path, chapters_file_path):
    print("Loading AI model (this takes a moment the first time)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 1. Load the JSON files
    with open(question_file_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    with open(chapters_file_path, 'r', encoding='utf-8') as f:
        chapters = json.load(f)
    
    # Initialize the output dictionary
    matched_list = {chapter["id"]: [] for chapter in chapters}
    
    # 2. Extract and format pure text for the AI
    chapter_texts = []
    for chapter in chapters:
        # Combine the title and the objectives into one rich string
        text = f"{chapter['title']}. {chapter['objectives']}"
        chapter_texts.append(text)
        
    question_texts = []
    for question in questions:
        # Combine the question text, options, and the image description!
        opts = " ".join(question.get("options", []))
        img_desc = question.get("image_description", "")
        text = f"{question['text']} {opts} {img_desc}"
        question_texts.append(text)
        
    # 3. Batch encode everything at once (MUCH faster)
    print("Generating vector embeddings...")
    chapter_embeddings = model.encode(chapter_texts, convert_to_tensor=True)
    question_embeddings = model.encode(question_texts, convert_to_tensor=True)
    
    # 4. Calculate similarities and assign
    print("Matching questions to chapters...")
    for i, question in enumerate(questions):
        # Compare THIS question's embedding to ALL chapter embeddings
        similarity_scores = util.cos_sim(question_embeddings[i], chapter_embeddings)[0]
        
        # Find the highest score
        best_match_index = similarity_scores.argmax().item()
        best_score = similarity_scores[best_match_index].item()
        best_chapter = chapters[best_match_index]
        
        # Optional: You can attach the score to the question so you know how confident the AI was!
        question["confidence_score"] = round(best_score, 3)
        question["matched_topic"] = best_chapter["title"]
        
        matched_list[best_chapter["id"]].append(question)
        
    return matched_list