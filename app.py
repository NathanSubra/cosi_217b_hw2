from flask import Flask, request, render_template_string, redirect, url_for
from notebook import Note, Comment, get_db

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Notes App</title>
    <style>
       body { font-family: Arial, sans-serif; }
       .note { border: 1px solid #ddd; padding: 10px; margin: 10px; border-radius: 5px; }
       .comments { margin-left: 20px; }
       .delete-button { background-color: red; color: white; border: none; padding: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Notes</h1>
    <div>
        {% for note in notes %}
            <div class="note">
                <strong>{{ note.title }}</strong> ({{ note.date_created.strftime("%Y-%m-%d %H:%M") }})<br>
                {{ note.content }}<br>
                <form method="post" action="{{ url_for('delete_note', note_id=note.id) }}">
                    <button type="submit" class="delete-button">Delete Note</button>
                </form>
                <h4>Comments:</h4>
                <ul class="comments">
                    {% for comment in note.comments %}
                        <li>{{ comment.content }} ({{ comment.date_created.strftime("%Y-%m-%d %H:%M") }})</li>
                    {% endfor %}
                </ul>
                <form method="post" action="{{ url_for('add_comment', note_id=note.id) }}">
                    <input type="text" name="comment_content" placeholder="Add a comment">
                    <button type="submit">Add Comment</button>
                </form>
            </div>
        {% endfor %}
    </div>

    <h2>Add Note</h2>
    <form method="post" action="{{ url_for('add_note') }}">
        Title: <input type="text" name="title"><br>
        Content: <textarea name="content"></textarea><br>
        <button type="submit">Add Note</button>
    </form>

    <h2>Search Notes</h2>
    <form method="get" action="{{ url_for('search') }}">
        Search: <input type="text" name="query">
        <button type="submit">Search</button>
    </form>

    {% if search_results is defined %}
        <h3>Search Results</h3>
        {% for note in search_results %}
            <div class="note">
                <strong>{{ note.title }}</strong> ({{ note.date_created.strftime("%Y-%m-%d %H:%M") }})<br>
                {{ note.content }}<br>
                <h4>Comments:</h4>
                <ul class="comments">
                    {% for comment in note.comments %}
                        <li>{{ comment.content }} ({{ comment.date_created.strftime("%Y-%m-%d %H:%M") }})</li>
                    {% endfor %}
                </ul>
            </div>
        {% endfor %}
    {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    db = next(get_db())
    notes = db.query(Note).all()
    return render_template_string(TEMPLATE, notes=notes)


@app.route("/add_note", methods=["POST"])
def add_note():
    title = request.form.get("title")
    content = request.form.get("content")
    db = next(get_db())
    if title and content:
        new_note = Note(title=title, content=content)
        db.add(new_note)
        db.commit()
    return redirect(url_for('home'))


@app.route("/delete_note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    db = next(get_db())
    note = db.query(Note).get(note_id)
    if note:
        db.delete(note)
        db.commit()
    return redirect(url_for('home'))


@app.route("/add_comment/<int:note_id>", methods=["POST"])
def add_comment(note_id):
    comment_content = request.form.get("comment_content")
    db = next(get_db())
    note = db.query(Note).get(note_id)
    if note and comment_content:
        new_comment = Comment(note_id=note.id, content=comment_content)
        db.add(new_comment)
        db.commit()
    return redirect(url_for('home'))


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()
    db = next(get_db())
    notes_by_title = db.query(Note).filter(Note.title.contains(query)).all()
    notes_by_content = db.query(Note).filter(Note.content.contains(query)).all()
    comments = db.query(Comment).filter(Comment.content.contains(query)).all()
    note_ids_from_comments = {comment.note_id for comment in comments}
    notes_from_comments = db.query(Note).filter(Note.id.in_(note_ids_from_comments)).all()
    # Combine results, using note IDs as key to avoid duplicates
    all_notes = {note.id: note for note in (notes_by_title + notes_by_content + notes_from_comments)}.values()
    return render_template_string(TEMPLATE, notes=db.query(Note).all(), search_results=all_notes)


if __name__ == "__main__":
    app.run(debug=True)
