import os
import json
import threading
from datetime import datetime
from flask import Flask, render_template, abort, g, flash, redirect, url_for
import psycopg2
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Set a secret key for flashing messages

DATABASE_CONFIG = {
    'dbname': 'granthamdb',     # your DB name
    'user': 'postgres',       # your DB user
    'password': 'root@123',   # your DB password
    'host': '35.246.37.125',  # Public IP of Cloud SQL instance
    'port': '5432'
}

# OpenAI API configuration
Key = "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"
client = OpenAI(api_key=Key)

def AI(query, model="gpt-4o-mini", max_tokens=2000, 
       system_prompt="Your responses must be 2000 words long"):
    """
    Sends a query to the OpenAI API with a system prompt to tune the assistant.
    Returns the assistant's response as a string.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        ai_message = response.to_dict()["choices"][0]["message"]["content"]
        return ai_message
    except Exception as e:
        return f"An error occurred in AI(): {e}"

def generate_dynamic_articles(n=10):
    """
    Generate n dynamic cybersecurity articles using OpenAI.
    The prompt instructs the AI to output a JSON object with keys:
    'title', 'author', 'content', and 'published_date' (formatted as YYYY-MM-DD).
    Returns a list of article dictionaries.
    """
    articles = []
    for i in range(n):
        prompt = (
            f"Generate a JSON object with keys 'title', 'author', 'content', and "
            f"'published_date' (YYYY-MM-DD) for a detailed cybersecurity article on a unique topic. "
            f"Ensure the article is informative, professional, and modern. Use topic number {i+1} to vary the content."
        )
        result = AI(prompt)
        try:
            article = json.loads(result)
        except Exception:
            # Fallback to a default article if JSON parsing fails.
            article = {
                "title": f"Sample Cybersecurity Article {i+1}",
                "author": "AI Generated",
                "content": result,
                "published_date": datetime.now().strftime("%Y-%m-%d")
            }
        # Convert the published_date string to a datetime object.
        try:
            article['published_date'] = datetime.strptime(article['published_date'], "%Y-%m-%d")
        except Exception:
            article['published_date'] = datetime.now()
        articles.append(article)
    return articles

def get_db_connection():
    """
    Get (or create) a database connection and store it in Flask's application context (g).
    """
    if 'db_conn' not in g:
        g.db_conn = psycopg2.connect(**DATABASE_CONFIG)
    return g.db_conn

@app.teardown_appcontext
def close_db_connection(exception):
    """
    Close the database connection at the end of the request.
    """
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()

def create_tables():
    """
    Create the 'articles' table if it doesn't already exist.
    """
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title VARCHAR(128) NOT NULL,
            author VARCHAR(64),
            content TEXT NOT NULL,
            published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def insert_dynamic_articles():
    """
    Insert dynamic articles into the 'articles' table.
    This function creates its own database connection (not relying on g) so that it can be safely used in a background thread.
    """
    articles = generate_dynamic_articles(n=10)  # Generate 10 dynamic articles
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()
    for article in articles:
        cursor.execute("""
            INSERT INTO articles (title, author, content, published_date)
            VALUES (%s, %s, %s, %s)
        """, (article['title'], article['author'], article['content'], article['published_date']))
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/refresh')
def refresh():
    """
    Route to trigger a background job to refresh (generate and insert) dynamic articles.
    The job is run in a separate thread so that the GUI is not delayed.
    """
    def background_refresh():
        with app.app_context():
            insert_dynamic_articles()
    
    thread = threading.Thread(target=background_refresh)
    thread.start()
    flash("Article refresh has been initiated in the background.", "info")
    return redirect(url_for('index'))

@app.route('/')
def index():
    """
    Route to display a list of articles fetched from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, author, content, published_date
        FROM articles
        ORDER BY published_date DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    # Convert rows (tuples) into dictionaries for template convenience.
    articles = []
    for row in rows:
        articles.append({
            'id': row[0],
            'title': row[1],
            'author': row[2],
            'content': row[3],
            'published_date': row[4]
        })
    return render_template('index.html', articles=articles)


@app.route('/#')
def under_progress():
    
    return "Under progress"

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    """
    Route to display details for a single article.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, author, content, published_date
        FROM articles
        WHERE id = %s
    """, (article_id,))
    row = cursor.fetchone()
    cursor.close()
    if row is None:
        abort(404)
    article = {
        'id': row[0],
        'title': row[1],
        'author': row[2],
        'content': row[3],
        'published_date': row[4]
    }
    return render_template('article_detail.html', article=article)
if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get('PORT', 5000))   # Render provides the PORT env var
    app.run(host='0.0.0.0', port=port)