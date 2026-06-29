import sqlite3
conn=sqlite3.connect("master_exam_data.db")
cur=conn.cursor()
cur.execute("DELETE FROM questions WHERE paper_name='ENGAA_2016_S1'")
conn.commit()
conn.close()
print("Deleted questions for ENGAA_2016_S1")
