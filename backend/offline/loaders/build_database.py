import sqlite3
import json
import os

def build_database(syllabus_json, classified_json, image_folder, db_name="exam_data.db"):
    print(f"Creating database: {db_name}...")
    
    # 1. Connect to SQLite (this automatically creates the file if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 2. Create the Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS syllabus (
            topic_id TEXT PRIMARY KEY,
            title TEXT,
            objectives TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_number INTEGER,
            topic_id TEXT,
            image_path TEXT,
            FOREIGN KEY(topic_id) REFERENCES syllabus(topic_id)
        )
    ''')
    
    # Clear out old data just in case you run this script multiple times
    cursor.execute('DELETE FROM syllabus')
    cursor.execute('DELETE FROM questions')
    
    # 3. Insert the Syllabus Data
    print("Loading Syllabus into database...")
    with open(syllabus_json, 'r', encoding='utf-8') as f:
        syllabus_data = json.load(f)
        for chapter in syllabus_data:
            cursor.execute('''
                INSERT INTO syllabus (topic_id, title, objectives)
                VALUES (?, ?, ?)
            ''', (chapter['id'], chapter['title'], chapter['objectives']))
            
    # 4. Insert the Question Data & Link Images
    print("Loading Questions into database...")
    with open(classified_json, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
        for q in questions_data:
            q_num = q['question_number']
            t_id = q['topic_id']
            
            # Construct where the image SHOULD be based on our slicing script
            img_path = os.path.join(image_folder, f"Question_{q_num}.png")
            
            # Optional: Check if the image actually exists!
            if not os.path.exists(img_path):
                print(f"⚠️ Warning: Image for Question {q_num} not found at {img_path}")
            
            cursor.execute('''
                INSERT INTO questions (question_number, topic_id, image_path)
                VALUES (?, ?, ?)
            ''', (q_num, t_id, img_path))
            
    # 5. Save (Commit) and Close
    conn.commit()
    conn.close()
    print("✅ Database built successfully!")

# ==========================================
# Run the Database Builder
# ==========================================
if __name__ == "__main__":
    # Update these paths if yours are named differently!
    SYLLABUS_FILE = "structured_syllabus.json" 
    CLASSIFIED_FILE = "classified_questions.json"
    IMAGE_DIR = "output_questions" 
    
    build_database(SYLLABUS_FILE, CLASSIFIED_FILE, IMAGE_DIR)