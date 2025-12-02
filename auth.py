import json
import streamlit as st
import os

# Path to the JSON file where user accounts are stored
USERS_FILE = os.path.join(os.path.dirname(__file__), "_users.json")


def load_users():
    """
    Load users from the JSON file.

    Returns:
        dict: A dictionary of users in the format:
              {
                  "username": {"password": "example"}
              }

    Notes:
        - Returns an empty dictionary if the file does not exist,
          is empty, or contains invalid JSON.
    """
    if os.path.exists(USERS_FILE) and os.stat(USERS_FILE).st_size != 0:
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupt or unreadable, return empty
            return {}
    return {}


def save_users(users_data):
    """
    Save the provided user dictionary to the JSON file.

    Args:
        users_data (dict): A dictionary of user data to write.
    """
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=4)


def authenticate(username, password):
    """
    Verify whether a username/password pair is valid.

    Args:
        username (str): The username to authenticate.
        password (str): The user's password.

    Returns:
        bool: True if credentials match a user in the database, False otherwise.
    """
    users = load_users()

    # Check if username exists and password matches
    if username in users and users[username]["password"] == password:
        return True

    return False


def login_screen():
    """
    Display the login interface.

    - Prompts the user for username and password.
    - Attempts to authenticate.
    - If successful, sets session_state["logged_in"] = True.
    - Provides a button to navigate to the signup screen.
    """
    st.title("Login or Sign Up to TigerPlate")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            # User successfully authenticated
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.subheader("Don't Have an Account?")
    
    # Switch to the signup screen
    if st.button("Sign Up"):
        st.session_state["screen"] = "signup"
        st.rerun()


def sign_up_screen():
    """
    Display the signup interface.

    - Prompts the user to input a new username and password.
    - Prevents duplicate usernames.
    - Saves the new user to the JSON file.
    - Redirects back to the login screen upon success.
    """
    st.title("Sign Up to TigerPlate")
    username = st.text_input("Create a Username")
    password = st.text_input("Create a Password", type="password")

    if st.button("Create Account"):
        users = load_users()

        # Prevent creation of accounts that already exist
        if username in users:
            st.error("Username already exists.")
            return

        # Require both fields to be filled in
        if not username or not password:
            st.warning("Username and password cannot be empty.")
            return

        # Add the new user to the database
        users[username] = {"password": password}
        save_users(users)

        st.success("Account created successfully.")

        # Return the user to the login page
        st.session_state["screen"] = "login"
        st.rerun()