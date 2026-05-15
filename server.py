# server.py
#
# ICS 32
# Assignment #3: The Distributed Social Platform
#
# This is the server code for the ICS 32 DSP server.
# You should not modify this file.

import socket
import json
import time
import uuid
import os
import sys
from pathlib import Path

# UNCOMMENT THE FOLLOWING LINES TO RUN THE FLASK SERVER
# from flask import Flask, render_template
# import threading

PORT1 = 3001
PORT2 = 3002

if len(sys.argv) > 1:
    PORT1 = int(sys.argv[1])
if len(sys.argv) > 2:
    PORT2 = int(sys.argv[2])

DATA_DIR = Path("dsp_data")
USERS_FILE = DATA_DIR / "users.json"
POSTS_FILE = DATA_DIR / "posts.json"


def init_storage():
    """Initialize the data directory and JSON files if they don't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({}))
    if not POSTS_FILE.exists():
        POSTS_FILE.write_text(json.dumps([]))


def load_users():
    """Load users from the users JSON file."""
    try:
        return json.loads(USERS_FILE.read_text())
    except Exception:
        return {}


def save_users(users):
    """Save users to the users JSON file."""
    USERS_FILE.write_text(json.dumps(users, indent=2))


def load_posts():
    """Load posts from the posts JSON file."""
    try:
        return json.loads(POSTS_FILE.read_text())
    except Exception:
        return []


def save_posts(posts):
    """Save posts to the posts JSON file."""
    POSTS_FILE.write_text(json.dumps(posts, indent=2))


def make_ok(message="", token=""):
    """Return a JSON ok response string."""
    return json.dumps({
        "response": {
            "type": "ok",
            "message": message,
            "token": token
        }
    })


def make_error(message=""):
    """Return a JSON error response string."""
    return json.dumps({
        "response": {
            "type": "error",
            "message": message
        }
    })


def handle_join(data, users):
    """Handle a join request. Register new user or authenticate existing."""
    try:
        username = data['join']['username']
        password = data['join']['password']
    except KeyError:
        return make_error("Malformed join request."), None, None

    if not username or not password:
        return make_error("Username and password required."), None, None

    if username in users:
        if users[username]['password'] != password:
            return make_error("Invalid password."), None, None
        token = str(uuid.uuid4())
        users[username]['token'] = token
        save_users(users)
        return make_ok(f"Welcome back, {username}", token), username, token
    else:
        token = str(uuid.uuid4())
        users[username] = {
            'password': password,
            'token': token,
            'bio': '',
            'biots': '',
            'posts': []
        }
        save_users(users)
        return make_ok(f"Welcome, {username}", token), username, token


def handle_post(data, users, username, token):
    """Handle a post request."""
    if username is None:
        return make_error("Not authenticated. Send join first.")

    try:
        stored_token = users[username]['token']
    except KeyError:
        return make_error("User not found.")

    if data.get('token') != stored_token:
        return make_error("Invalid token.")

    try:
        entry = data['post']['entry']
        timestamp = data['post'].get('timestamp', str(time.time()))
    except KeyError:
        return make_error("Malformed post request.")

    if not entry or not entry.strip():
        return make_error("Post entry must not be empty.")

    server_timestamp = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(time.time())
    )
    post_obj = {
        'entry': entry,
        'timestamp': server_timestamp,
        'user': username
    }

    posts = load_posts()
    posts.insert(0, post_obj)
    save_posts(posts)

    users[username]['posts'].insert(0, post_obj)
    save_users(users)

    return make_ok("Post published.")


def handle_bio(data, users, username, token):
    """Handle a bio update request."""
    if username is None:
        return make_error("Not authenticated. Send join first.")

    try:
        stored_token = users[username]['token']
    except KeyError:
        re