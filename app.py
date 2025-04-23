import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import hashlib  # For password hashing

# Connect to MongoDB
client = MongoClient("mongodb+srv://Notesdb:yPr18ws3Vd5S8Yh5@cluster0.cvafqb8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["notes_db"]
users_collection = db["users"]  # User accounts collection
notes_collection = db["notes"]  # Notes collection

# Initialize session state variables
if "user" not in st.session_state:
    st.session_state["user"] = None
if "selected_note" not in st.session_state:
    st.session_state["selected_note"] = None
if "mode" not in st.session_state:
    st.session_state["mode"] = "login"  # Default mode is login


# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Function to check login credentials
def authenticate_user(username, password):
    user = users_collection.find_one({"username": username, "password": hash_password(password)})
    return user is not None


# Function to create a new user account and auto-login
def register_user(username, password):
    if users_collection.find_one({"username": username}):
        return False  # User already exists
    users_collection.insert_one({"username": username, "password": hash_password(password)})
    st.session_state["user"] = username  # Auto-login after sign-up
    return True


# User Authentication UI
st.markdown("<style>body { text-align: center; }</style>", unsafe_allow_html=True)

if st.session_state["mode"] == "login":
    st.title("🔒 Login to Your Notes")

    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔑 Login"):
            if authenticate_user(username, password):
                st.session_state["user"] = username
                st.session_state["mode"] = "view"
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    with col2:
        if st.button("🆕 Sign Up"):
            st.session_state["mode"] = "signup"
            st.rerun()

elif st.session_state["mode"] == "signup":
    st.title("📝 Sign Up for a New Account")

    new_username = st.text_input("Choose a Username", placeholder="Pick a username")
    new_password = st.text_input("Choose a Password", type="password", placeholder="Create a password")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✅ Register"):
            if new_username and new_password:
                if register_user(new_username, new_password):
                    st.success(f"🎉 Account created! Welcome, {new_username}!")
                    st.session_state["mode"] = "view"  # Auto-login after registration
                    st.rerun()
                else:
                    st.error("⚠️ Username already exists. Try a different one.")
            else:
                st.warning("⚠️ Username and Password cannot be empty.")

    with col2:
        if st.button("🔙 Back to Login"):
            st.session_state["mode"] = "login"
            st.rerun()

# If logged in, show the note-taking app
if st.session_state["user"]:
    st.title(f"📝 Welcome, {st.session_state['user']}")

    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state["user"] = None
        st.session_state["mode"] = "login"
        st.rerun()

    # Sidebar for notes list
    st.sidebar.title("🗂️ Your Notes")
    st.sidebar.write("📌 Select a note to view/edit or click **'➕ Add Note'** to create a new one.")

    # Fetch all notes for the logged-in user
    notes = list(notes_collection.find({"username": st.session_state["user"]}).sort("date", -1))
    titles = {str(note["_id"]): note["title"] for note in notes}

    # "Add Note" Button
    if st.sidebar.button("➕ Add Note"):
        st.session_state["selected_note"] = None
        st.session_state["mode"] = "create"
        st.rerun()

    # Sidebar Note Selection (only if notes exist)
    if notes and st.session_state["mode"] != "create":
        selected_id = st.sidebar.radio("📌 Select a Note:", list(titles.keys()), format_func=lambda x: titles[x])

        if selected_id and st.session_state["selected_note"] != selected_id:
            st.session_state["selected_note"] = selected_id
            st.session_state["mode"] = "edit"
            st.rerun()

    # CREATE NEW NOTE
    if st.session_state["mode"] == "create":
        st.subheader("📝 Add a New Note")
        title = st.text_input("Title", placeholder="Enter note title")
        content = st.text_area("Write your note here...", placeholder="Start typing your note...")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("💾 Save Note"):
                if title.strip():
                    note = {"username": st.session_state["user"], "title": title.strip(), "content": content.strip(), "date": datetime.now()}
                    new_id = notes_collection.insert_one(note).inserted_id
                    st.session_state["selected_note"] = str(new_id)
                    st.session_state["mode"] = "edit"
                    st.rerun()
                else:
                    st.warning("⚠️ Title cannot be empty!")

        with col2:
            if st.button("❌ Cancel"):
                st.session_state["mode"] = "view"
                st.rerun()

    # UPDATE OR DELETE EXISTING NOTE
    elif st.session_state["mode"] == "edit":
        st.subheader("✏️ Editing Note")

        note = notes_collection.find_one({"_id": ObjectId(st.session_state["selected_note"])})
        if note:
            new_title = st.text_input("Edit Title", value=note["title"], placeholder="Update title")
            new_content = st.text_area("Edit Content", value=note["content"], placeholder="Update your note")

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("💾 Update Note"):
                    notes_collection.update_one(
                        {"_id": ObjectId(st.session_state["selected_note"])},
                        {"$set": {"title": new_title.strip(), "content": new_content.strip(), "date": datetime.now()}}
                    )
                    st.success("✅ Note updated successfully!")
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete Note"):
                    notes_collection.delete_one({"_id": ObjectId(st.session_state["selected_note"])})
                    st.session_state["selected_note"] = None
                    st.session_state["mode"] = "view"
                    st.warning("⚠️ Note deleted!")
                    st.rerun()
        else:
            st.error("🚨 Error: Note not found. It might have been deleted.")
            st.session_state["selected_note"] = None
            st.session_state["mode"] = "view"
            st.rerun()
