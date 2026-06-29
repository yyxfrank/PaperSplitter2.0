import sqlite3
import json
import os

def append_to_database(paper_name, syllabus_json, classified_json, image_folder, db_name="master_exam_data.db"):
    print(f"Opening Master Database: {db_name}...")
    
    # 1. Connect to SQLite
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 2. Create the Tables (if this is the very first time running it)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS syllabus (
            topic_id TEXT PRIMARY KEY,
            title TEXT,
            objectives TEXT
        )
    ''')
    
    # Notice we added a 'paper_name' column here!
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_name TEXT,
            question_number INTEGER,
            topic_id TEXT,
            image_path TEXT,
            FOREIGN KEY(topic_id) REFERENCES syllabus(topic_id),
            UNIQUE (paper_name, question_number)
        )
    ''')
    
    # WE REMOVED THE 'DELETE FROM' COMMANDS HERE!
    
    # 3. Insert the Syllabus Data (Safely)
    print("Syncing Syllabus...")
    with open(syllabus_json, 'r', encoding='utf-8') as f:
        syllabus_data = json.load(f)
        for chapter in syllabus_data:
            # INSERT OR IGNORE means: If P1.1 is already in the database, just skip it!
            cursor.execute('''
                INSERT OR IGNORE INTO syllabus (topic_id, title, objectives)
                VALUES (?, ?, ?)
            ''', (chapter['id'], chapter['title'], chapter['objectives']))
            
    # 4. Insert the New Questions
    print(f"Adding questions from {paper_name}...")
    with open(classified_json, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
        
        # Keep track of how many we add
        added_count = 0 
        
        for q in questions_data:
            q_num = q['question_number']
            t_id = q['topic_id']
            
            # Construct the path: e.g., output_questions/ENGAA_2016/Question_1.png
            img_path = os.path.join(image_folder, paper_name, f"Question_{q_num}.png")
            
            # Convert Windows backslashes to forward slashes for web compatibility
            img_path = img_path.replace("\\", "/")
            
            # Insert the new question, attaching the paper_name to it!
            cursor.execute('''
                INSERT INTO questions (paper_name, question_number, topic_id, image_path)
                VALUES (?, ?, ?, ?) ON CONFLICT(paper_name, question_number) DO UPDATE 
                SET image_path = excluded.image_path, topic_id=excluded.topic_id
            ''', (paper_name, q_num, t_id, img_path))
            
            added_count += 1
            
    # 5. Save and Close
    conn.commit()
    conn.close()
    print(f"✅ Successfully appended {added_count} questions from {paper_name} into the Master Database!")

# ==========================================
# Run the Database Appender
# ==========================================
if __name__ == "__main__":
    # Every time you process a new paper, just update these variables and run the script!
    PAPER_IDENTIFIER = "ENGAA_2016_S1"  # Next time, change this to "ENGAA_2017"
    SYLLABUS_FILE = "structured_syllabus_physics.json" 
    CLASSIFIED_FILE = "classified_questions_physics.json" # The JSON you just got from Gemini
    IMAGE_DIR = "output_questions" 
    
    append_to_database(PAPER_IDENTIFIER, SYLLABUS_FILE, CLASSIFIED_FILE, IMAGE_DIR)