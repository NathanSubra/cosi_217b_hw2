import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("Notes App")

# --- Add Note Section ---
st.header("Add a Note")
with st.form(key="add_note_form"):
    note_title = st.text_input("Title")
    note_content = st.text_area("Content")
    add_note_button = st.form_submit_button("Add Note")

if add_note_button:
    if note_title and note_content:
        try:
            response = requests.post(
                f"{API_URL}/notes/",
                params={"title": note_title, "content": note_content},
            )
            if response.status_code == 200:
                st.success(response.json()["message"])
            else:
                st.error(response.json().get("detail", "Error adding note"))
        except requests.exceptions.ConnectionError:
            st.error("Unable to connect to the backend server. Please ensure that the FastAPI server is running on port 8000.")
    else:
        st.error("Both title and content are required.")

# --- Search Section ---
st.header("Search Notes")
with st.form(key="search_form"):
    search_query = st.text_input("Search")
    search_button = st.form_submit_button("Search")

if search_button:
    try:
        response = requests.get(f"{API_URL}/search/", params={"query": search_query})
        if response.status_code == 200:
            try:
                notes = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error("Error decoding JSON from response. Raw response text:")
                st.error(response.text)
                notes = []

            if notes:
                for note in notes:
                    st.subheader(f"{note['title']} (ID: {note['id']})")
                    st.write(note["content"])
                    st.write("Comments:")
                    for comment in note["comments"]:
                        st.write(f"- {comment['content']} (ID: {comment['id']})")
            else:
                st.info("No notes found.")
        else:
            st.error("Error searching notes.")
    except requests.exceptions.ConnectionError:
        st.error("Unable to connect to the backend server. Please ensure that the FastAPI server is running on port 8000.")

# --- Display All Notes ---
st.header("All Notes")
try:
    response = requests.get(f"{API_URL}/notes/")
    if response.status_code == 200:
        try:
            notes = response.json()
        except requests.exceptions.JSONDecodeError:
            st.error("Error decoding JSON from response. Raw response text:")
            st.error(response.text)
            notes = []

        for note in notes:
            with st.expander(f"{note['title']} (ID: {note['id']})"):
                st.write(note["content"])
                st.write("Created at:", note["date_created"])
                st.write("Comments:")
                for comment in note["comments"]:
                    st.write(f"- {comment['content']} (Created at: {comment['date_created']})")
                # Form to add a comment
                with st.form(key=f"add_comment_{note['id']}"):
                    comment_content = st.text_input("Add a comment", key=f"comment_{note['id']}")
                    submit_comment = st.form_submit_button("Submit Comment")
                    if submit_comment and comment_content:
                        try:
                            r = requests.post(f"{API_URL}/notes/{note['id']}/comments", params={"content": comment_content})
                            if r.status_code == 200:
                                st.success("Comment added!")
                                st.experimental_rerun()
                            else:
                                st.error("Error adding comment.")
                        except requests.exceptions.ConnectionError:
                            st.error("Unable to connect to the backend server. Please ensure that the FastAPI server is running on port 8000.")
                # Delete note button
                if st.button("Delete Note", key=f"delete_{note['id']}"):
                    try:
                        r = requests.delete(f"{API_URL}/notes/{note['id']}")
                        if r.status_code == 200:
                            st.success("Note deleted!")
                            st.experimental_rerun()
                        else:
                            st.error("Error deleting note.")
                    except requests.exceptions.ConnectionError:
                        st.error("Unable to connect to the backend server. Please ensure that the FastAPI server is running on port 8000.")
    else:
        st.error("Error fetching notes.")
except requests.exceptions.ConnectionError:
    st.error("Unable to connect to the backend server. Please ensure that the FastAPI server is running on port 8000.")
