# "Database code" for the DB Forum.

import datetime
import psycopg2


# Get posts from database

def get_posts():
  # Connect to database.
  db = psycopg2.connect("dbname=forum")
  # Create cursor to sort
  c = db.cursor()
  """Return all posts from the 'database', most recent first."""
  c.execute("SELECT time, content FROM posts order by time DESC")
  posts = ({'content': str(row[1]), 'time': str(row[0])}
           for row in c.fetchall())
  db.close()
  return posts

# Add Post to Database

def add_post(content):
  """Add a post to the 'database' with the current timestamp."""
  db = psycopg2.connect("dbname=forum")
  c = db.cursor()
  c.execute("INSERT INTO posts (content) VALUES ('%s')" % content)
  db.commit()
  db.close()
