from sentence_transformers import SentenceTransformer, util

def match_question_to_chapter(question, chapters):
    """
    Takes a single question and a list of chapters, returning the best match.
    """
    # 1. Load a pre-trained, lightweight NLP model
    # 'all-MiniLM-L6-v2' is fast and great for general semantic similarity
    print("Loading AI model (this takes a moment the first time)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 2. Convert text into vector embeddings
    question_embedding = model.encode(question)
    chapter_embeddings = model.encode(chapters)
    
    # 3. Calculate "Cosine Similarity" (how close the vectors are to each other)
    # This returns a score between 0 (completely unrelated) and 1 (exact match)
    similarity_scores = util.cos_sim(question_embedding, chapter_embeddings)[0]
    
    # 4. Find the chapter with the highest score
    best_match_index = similarity_scores.argmax().item()
    best_score = similarity_scores[best_match_index].item()
    best_chapter = chapters[best_match_index]
    
    return best_chapter, best_score

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # Simulated data from your extracted syllabus
    syllabus_chapters = [
        "Chapter 1: Cellular Biology and Mitosis",
        "Chapter 2: Kinematics, Velocity, and Acceleration",
        "Chapter 3: Macroeconomics and Supply Chain",
        "Chapter 4: Organic Chemistry and Hydrocarbons"
    ]
    
    # A simulated question sliced from a past paper
    # Notice it doesn't use the words "Kinematics", "Velocity", or "Acceleration"
    past_paper_question = "If a car drops off a cliff and falls for 4 seconds, how fast is it traveling right before impact?"
    
    print(f"Question: '{past_paper_question}'\n")
    
    best_chapter, score = match_question_to_chapter(past_paper_question, syllabus_chapters)
    
    print(f"Best Match: {best_chapter}")
    print(f"Confidence Score: {score:.4f} (Out of 1.0)")