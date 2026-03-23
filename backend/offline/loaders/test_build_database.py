import sqlite3

# Connect to our newly created database
conn = sqlite3.connect("exam_data.db")
cursor = conn.cursor()

# Let's pretend a student clicked on chapter P1.1 on the website
target_topic = "P1.2"

print(f"\n🔍 Searching for questions in Topic {target_topic}...\n")

# A SQL JOIN query: Gets the image path and the chapter title together!
cursor.execute('''
    SELECT syllabus.title, questions.question_number, questions.image_path 
    FROM questions
    JOIN syllabus ON questions.topic_id = syllabus.topic_id
    WHERE questions.topic_id = ?
''', (target_topic,))

results = cursor.fetchall()

if not results:
    print("No questions found for this topic.")
else:
    for row in results:
        chapter_title = row[0]
        q_num = row[1]
        img_path = row[2]
        print(f"[{chapter_title}] -> Found Question {q_num} located at: {img_path}")

conn.close()