import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import hashlib

# Connect to MongoDB
client = MongoClient("mongodb+srv://Notesdb:yPr18ws3Vd5S8Yh5@cluster0.cvafqb8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["notes_db"]
users_collection = db["users"]
notes_collection = db["notes"]

# Initialize session state
if "user" not in st.session_state:
    st.session_state["user"] = None
if "selected_note" not in st.session_state:
    st.session_state["selected_note"] = None
if "mode" not in st.session_state:
    st.session_state["mode"] = "login"

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    user = users_collection.find_one({"username": username, "password": hash_password(password)})
    return user is not None

def register_user(username, password):
    if users_collection.find_one({"username": username}):
        return False
    users_collection.insert_one({"username": username, "password": hash_password(password)})
    st.session_state["user"] = username
    return True

# Login & Sign-up UI
if st.session_state["mode"] == "login":
    st.title("🔒 Login to Your Notes")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Login"):
            if authenticate_user(username, password):
                st.session_state["user"] = username
                st.session_state["mode"] = "view"
                st.rerun()
            else:
                st.error("Invalid username or password.")
    with col2:
        if st.button("🆕 Sign Up"):
            st.session_state["mode"] = "signup"
            st.rerun()

elif st.session_state["mode"] == "signup":
    st.title("📝 Sign Up")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Register"):
            if new_username and new_password:
                if register_user(new_username, new_password):
                    st.success("Account created!")
                    st.session_state["mode"] = "view"
                    st.rerun()
                else:
                    st.error("Username already exists.")
            else:
                st.warning("Fields can't be empty.")
    with col2:
        if st.button("🔙 Back"):
            st.session_state["mode"] = "login"
            st.rerun()

# Main Notes Interface
if st.session_state["user"]:
    st.title(f"📝 Welcome, {st.session_state['user']}")

    # Logout
    if st.sidebar.button("🚪 Logout"):
        st.session_state["user"] = None
        st.session_state["mode"] = "login"
        st.rerun()

    # Load notes
    notes = list(notes_collection.find({"username": st.session_state["user"]}).sort("date", -1))
    titles = {str(note["_id"]): note["title"] for note in notes}

    # Sidebar: Note selection
    st.sidebar.title("🗂️ Your Notes")
    st.sidebar.write("📌 Select a note or add a new one.")
    if st.sidebar.button("➕ Add Note"):
        st.session_state["mode"] = "create"
        st.session_state["selected_note"] = None
        st.rerun()

    if notes and st.session_state["mode"] != "create":
        selected_id = st.sidebar.radio("📌 Select a Note:", list(titles.keys()), format_func=lambda x: titles[x])
        if selected_id and st.session_state["selected_note"] != selected_id:
            st.session_state["selected_note"] = selected_id
            st.session_state["mode"] = "edit"
            st.rerun()

    # Main content area
    if st.session_state["mode"] == "view":
        if not notes:
            st.info("👋 You don't have any notes yet.")
            if st.button("➕ Create your first note"):
                st.session_state["mode"] = "create"
                st.rerun()
        else:
            st.info("📌 Select a note from the sidebar to view or edit it.")

    elif st.session_state["mode"] == "create":
        st.subheader("📝 Add a New Note")
        title = st.text_input("Note Title")
        content = st.text_area("Note Content")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save"):
                if title.strip():
                    note = {
                        "username": st.session_state["user"],
                        "title": title.strip(),
                        "content": content.strip(),
                        "date": datetime.now()
                    }
                    note_id = notes_collection.insert_one(note).inserted_id
                    st.session_state["selected_note"] = str(note_id)
                    st.session_state["mode"] = "edit"
                    st.rerun()
                else:
                    st.warning("Title cannot be empty.")
        with col2:
            if st.button("❌ Cancel"):
                st.session_state["mode"] = "view"
                st.rerun()

    elif st.session_state["mode"] == "edit":
        note = notes_collection.find_one({"_id": ObjectId(st.session_state["selected_note"])})
        if note:
            st.subheader("✏️ Edit Note")
            new_title = st.text_input("Edit Title", value=note["title"])
            new_content = st.text_area("Edit Content", value=note["content"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Update"):
                    notes_collection.update_one(
                        {"_id": ObjectId(st.session_state["selected_note"])},
                        {"$set": {
                            "title": new_title.strip(),
                            "content": new_content.strip(),
                            "date": datetime.now()
                        }}
                    )
                    st.success("Note updated.")
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete"):
                    notes_collection.delete_one({"_id": ObjectId(st.session_state["selected_note"])})
                    st.session_state["selected_note"] = None
                    st.session_state["mode"] = "view"
                    st.warning("Note deleted.")
                    st.rerun()
        else:
            st.error("Note not found.")
            st.session_state["mode"] = "view"
            st.rerun()
