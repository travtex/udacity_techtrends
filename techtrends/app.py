import sqlite3
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
import sys

# Count number of DB connections
connections_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global connections_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connections_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error('Post with ID "{id}" not found.'.format(id=post_id))
      return render_template('404.html'), 404
    else:
      app.logger.info('Post titled "{post_title}" accessed.'.format(post_title=post['title']))
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

# Define the healthz route
@app.route('/healthz')
def healthcheck():
    try:
        connection = get_db_connection()
        connection.execute('SELECT COUNT(*) FROM posts')
        connection.close()
        r = {'result': 'OK - healthy'}
    except Exception:
        r = {'result': 'ERR - not healthy'}
    return json.dumps(r)

# Define the metrics route
@app.route('/metrics')
def get_metrics():
    try:
        connection = get_db_connection()
        posts = connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        r = {'db_connection_count': connections_count, 'post_count': len(posts)}
    except Exception:
        r = {'ERR - Metrics generation failed.'}
    return json.dumps(r)

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%m/%d/%Y, %H:%M:%S',
        handlers=[sys.stderr, sys.stdout]
    )
    app.run(host='0.0.0.0', port='3111')
