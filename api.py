from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from notebook import Note, Comment, get_db

app = FastAPI()

@app.post("/notes/")
def create_note(title: str, content: str, db: Session = Depends(get_db)):
    existing_note = db.query(Note).filter(Note.title == title).first()
    if existing_note:
        raise HTTPException(status_code=400, detail="Note with this title already exists.")
    new_note = Note(title=title, content=content)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return {"message": f"Note '{new_note.title}' added successfully!", "id": new_note.id}

@app.get("/notes/")
def get_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "date_created": note.date_created,
            "comments": [
                {"id": c.id, "content": c.content, "date_created": c.date_created}
                for c in note.comments
            ],
        }
        for note in notes
    ]

@app.get("/notes/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "date_created": note.date_created,
        "comments": [
            {"id": c.id, "content": c.content, "date_created": c.date_created}
            for c in note.comments
        ],
    }

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"message": f"Note '{note.title}' and its comments deleted!"}

@app.post("/notes/{note_id}/comments")
def add_comment(note_id: int, content: str, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    new_comment = Comment(note_id=note.id, content=content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return {"message": "Comment added successfully!", "comment_id": new_comment.id}

@app.get("/search/")
def search_notes(query: str, db: Session = Depends(get_db)):
    notes_by_title = db.query(Note).filter(Note.title.contains(query)).all()
    notes_by_content = db.query(Note).filter(Note.content.contains(query)).all()
    comments = db.query(Comment).filter(Comment.content.contains(query)).all()
    note_ids_from_comments = {comment.note_id for comment in comments}
    notes_from_comments = db.query(Note).filter(Note.id.in_(note_ids_from_comments)).all()
    # Combine results and remove duplicates
    all_notes = {note.id: note for note in (notes_by_title + notes_by_content + notes_from_comments)}.values()
    return [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "date_created": note.date_created,
            "comments": [
                {"id": c.id, "content": c.content, "date_created": c.date_created}
                for c in note.comments
            ],
        }
        for note in all_notes
    ]
