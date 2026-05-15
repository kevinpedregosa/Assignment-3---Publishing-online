# Kevin Noel Pedregosa
# pedregok@uci.edu
# 18447962

# ui.py
# Handles all command processing for the Journal program.
# Supports both admin mode commands and friendly UI interactions.

import shlex
from pathlib import Path
from Profile import Profile, Post, DsuFileError, DsuProfileError
import ds_client

# Module-level state: the currently loaded profile and its file path
current_profile = None
current_path = None


def is_valid_dsu(path):
    """Return True if path exists, is a file, and has .dsu extension."""
    p = Path(path)
    return p.exists() and p.is_file() and p.suffix == '.dsu'


def handle_create(tokens, admin=False):
    """Handle the C command: create a new DSU file and collect profile info.

    Format: C <directory> -n <filename>
    If the file already exists, load it instead of raising an error.
    """
    global current_profile, current_path

    if len(tokens) != 4 or tokens[2] != '-n':
        print("ERROR: Usage: C <directory> -n <filename>")
        return

    dir_path = Path(tokens[1])
    name = tokens[3]

    if not dir_path.exists() or not dir_path.is_dir():
        print("ERROR: Directory does not exist.")
        return

    file_path = dir_path / f"{name}.dsu"

    if file_path.exists():
        print(f"File already exists. Loading {file_path} instead.")
        _load_profile(str(file_path))
        return

    try:
        file_path.touch()
        print(f"Created: {file_path}")
        current_path = str(file_path)
        current_profile = Profile()
        _collect_profile_info(admin)
    except Exception as e:
        print(f"ERROR: Could not create file. {e}")


def _save_profile():
    """Save the current profile to the current path."""
    global current_profile, current_path
    if current_profile is None or current_path is None:
        return
    try:
        current_profile.save_profile(current_path)
    except DsuFileError as e:
        print(f"ERROR: Could not save profile. {e}")


def _load_profile(path):
    """Load a profile from a DSU file path string."""
    global current_profile, current_path
    p = Path(path)
    if not p.exists() or p.suffix != '.dsu':
        print("ERROR: Invalid DSU file path.")
        return
    try:
        profile = Profile()
        profile.load_profile(path)
        current_profile = profile
        current_path = path
        print(f"Loaded profile for user '{profile.username}'.")
    except DsuProfileError as e:
        print(f"ERROR: File is not a valid DSU format. {e}")
    except DsuFileError as e:
        print(f"ERROR: Could not open file. {e}")


def _collect_profile_info(admin=False):
    """Prompt the user for username, password, bio, and server, then save.

    In admin mode, input() reads values without descriptive prompt strings.
    """
    global current_profile, current_path

    if admin:
        username = input()
        password = input()
        bio = input()
        dsuserver = input()
    else:
        print("Please enter your profile details.")
        username = input("  Username (no spaces): ").strip()
        password = input("  Password (no spaces): ").strip()
        bio = input("  Bio (optional): ").strip()
        dsuserver = input(
            "  DSP Server address (e.g. 127.0.0.1): "
        ).strip()

    if not username or ' ' in username:
        print("ERROR: Username must not be empty or contain spaces.")
        current_profile = None
        current_path = None
        return

    if not password or ' ' in password:
        print("ERROR: Password must not be empty or contain spaces.")
        current_profile = None
        current_path = None
        return

    if not dsuserver:
        dsuserver = '127.0.0.1'

    current_profile.username = username
    current_profile.password = password
    current_profile.bio = bio
    current_profile.dsuserver = dsuserver

    _save_profile()
    print(f"Profile saved for user '{username}'.")


def handle_open(tokens):
    """Handle the O command: open and load an existing DSU file.

    Format: O <filepath>
    """
    if len(tokens) != 2:
        print("ERROR: Usage: O <filepath.dsu>")
        return
    _load_profile(tokens[1])


def handle_read(tokens):
    """Handle the R command: read raw contents of a DSU file.

    Format: R <filepath>
    """
    if len(tokens) != 2:
        print("ERROR: Usage: R <filepath.dsu>")
        return
    path = Path(tokens[1])
    if not is_valid_dsu(path):
        print("ERROR: Invalid or non-existent DSU file.")
        return
    try:
        content = path.read_text()
        if not content.strip():
            print("EMPTY")
        else:
            print(content, end="")
    except Exception as e:
        print(f"ERROR: Could not read file. {e}")


def handle_delete(tokens):
    """Handle the D command: delete a DSU file.

    Format: D <filepath>
    """
    global current_profile, current_path

    if len(tokens) != 2:
        print("ERROR: Usage: D <filepath.dsu>")
        return
    path = Path(tokens[1])
    if not is_valid_dsu(path):
        print("ERROR: Invalid or non-existent DSU file.")
        return
    try:
        path.unlink()
        print(f"{path} DELETED")
        if current_path == str(path):
            current_profile = None
            current_path = None
    except Exception as e:
        print(f"ERROR: Could not delete file. {e}")


def _require_profile():
    """Return False and print error if no profile is currently loaded."""
    if current_profile is None:
        print("ERROR: No DSU file loaded. Use C to create or O to open one.")
        return False
    return True


def handle_edit(tokens):
    """Handle the E command: edit fields of the currently loaded profile.

    Format: E [-usr VAL] [-pwd VAL] [-bio VAL] [-addpost VAL] [-delpost ID]
    Options may be combined in any order.
    """
    if not _require_profile():
        return

    i = 1
    while i < len(tokens):
        option = tokens[i]

        if option in ('-usr', '-pwd', '-bio', '-addpost', '-delpost'):
            if i + 1 >= len(tokens):
                print(f"ERROR: Option {option} requires a value.")
                return
            value = tokens[i + 1]
            i += 2
        else:
            print(f"ERROR: Unknown option '{option}'.")
            return

        if option == '-usr':
            if not value or ' ' in value:
                print("ERROR: Username must not be empty or contain spaces.")
                return
            current_profile.username = value
            _save_profile()
            print(f"Username updated to '{value}'.")

        elif option == '-pwd':
            if not value or ' ' in value:
                print("ERROR: Password must not be empty or contain spaces.")
                return
            current_profile.password = value
            _save_profile()
            print("Password updated.")

        elif option == '-bio':
            if not value.strip():
                print("ERROR: Bio must not be empty or whitespace.")
                return
            current_profile.bio = value
            _save_profile()
            print("Bio updated.")

        elif option == '-addpost':
            if not value.strip():
                print("ERROR: Post entry must not be empty or whitespace.")
                return
            post = Post(value)
            current_profile.add_post(post)
            _save_profile()
            print("Post added.")

        elif option == '-delpost':
            try:
                index = int(value)
            except ValueError:
                print("ERROR: Post ID must be an integer.")
                return
            if not current_profile.del_post(index):
                print(f"ERROR: No post found at index {index}.")
                return
            _save_profile()
            print(f"Post {index} deleted.")


def handle_print(tokens):
    """Handle the P command: print profile data to the screen.

    Format: P [-usr] [-pwd] [-bio] [-posts] [-post ID] [-all]
    """
    if not _require_profile():
        return

    i = 1
    while i < len(tokens):
        option = tokens[i]

        if option == '-usr':
            print(f"Username: {current_profile.username}")
            i += 1

        elif option == '-pwd':
            print(f"Password: {current_profile.password}")
            i += 1

        elif option == '-bio':
            print(f"Bio: {current_profile.bio}")
            i += 1

        elif option == '-posts':
            posts = current_profile.get_posts()
            if not posts:
                print("No posts found.")
            else:
                for idx, post in enumerate(posts):
                    print(f"[{idx}] {post.entry}")
            i += 1

        elif option == '-post':
            if i + 1 >= len(tokens):
                print("ERROR: -post requires an ID.")
                return
            try:
                index = int(tokens[i + 1])
            except ValueError:
                print("ERROR: Post ID must be an integer.")
                return
            posts = current_profile.get_posts()
            if index < 0 or index >= len(posts):
                print(f"ERROR: No post at index {index}.")
                return
            post = posts[index]
            print(f"[{index}] {post.entry}")
            print(f"      timestamp: {post.timestamp}")
            i += 2

        elif option == '-all':
            print(f"Username: {current_profile.username}")
            print(f"Password: {current_profile.password}")
            print(f"Bio: {current_profile.bio}")
            print(f"DSP Server: {current_profile.dsuserver}")
            posts = current_profile.get_posts()
            if not posts:
                print("Posts: (none)")
            else:
                print("Posts:")
                for idx, post in enumerate(posts):
                    print(f"  [{idx}] {post.entry}")
                    print(f"        timestamp: {post.timestamp}")
            i += 1

        else:
            print(f"ERROR: Unknown option '{option}'.")
            return


def handle_publish(port: int = 3001):
    """Publish a post and/or bio to the DSP server.

    Prompts the user to choose what to publish, validates input,
    and calls ds_client.send. Uses the server stored in the profile.
    """
    if not _require_profile():
        return

    if not current_profile.dsuserver:
        print("ERROR: No DSP server configured in profile.")
        return

    print("\n  What would you like to publish?")
    print("  [1] A new post")
    print("  [2] My bio")
    print("  [3] Both a post and my bio")
    choice = input("  Enter choice (1/2/3): ").strip()

    message = ''
    bio = None

    if choice in ('1', '3'):
        message = input("  Enter post message: ").strip()
        if not message:
            print("ERROR: Post message must not be empty or whitespace.")
            return

    if choice in ('2', '3'):
        bio = input("  Enter bio: ").strip()
        if not bio:
            print("ERROR: Bio must not be empty or whitespace.")
            return

    if choice not in ('1', '2', '3'):
        print("ERROR: Invalid choice.")
        return

    print("  Connecting to DSP server...")
    result = ds_client.send(
        current_profile.dsuserver,
        port,
        current_profile.username,
        current_profile.password,
        message,
        bio
    )

    if result:
        print("  Successfully published to DSP server!")
        if message:
            post = Post(message)
            current_profile.add_post(post)
            _save_profile()
    else:
        print("  ERROR: Failed to publish to DSP server.")


def _dispatch(tokens, admin=False):
    """Dispatch a parsed token list to the correct command handler."""
    if not tokens:
        return
    command = tokens[0]
    if command == 'C':
        handle_create(tokens, admin=admin)
    elif command == 'O':
        handle_open(tokens)
    elif command == 'R':
        handle_read(tokens)
    elif command == 'D':
        handle_delete(tokens)
    elif command == 'E':
        handle_edit(tokens)
    elif command == 'P':
        handle_print(tokens)
    elif command == 'Q':
        return 'quit'
    else:
        print("ERROR: Unknown command.")


def run_admin():
    """Run the program in admin mode.

    Only raw input commands are accepted; no friendly prompts are shown.
    """
    print("Admin mode active. Enter commands (Q to quit).")
    while True:
        try:
            user_input = input()
            if not user_input.strip():
                print("ERROR")
                continue
            try:
                tokens = shlex.split(user_input)
            except ValueError:
                print("ERROR")
                continue
            result = _dispatch(tokens, admin=True)
            if result == 'quit':
                break
        except EOFError:
            break


def run_ui():
    """Run the program with the friendly user interface."""
    print("\n--- ICS 32 Journal ---")
    print("Commands: [c] Create  [o] Open  [e] Edit"
          "  [p] Print  [s] Publish  [q] Quit")

    while True:
        choice = input("\n> What would you like to do? ").strip().lower()

        if choice == 'q':
            print("Goodbye!")
            break

        elif choice == 'c':
            directory = input("  Enter directory path: ").strip()
            name = input("  Enter journal name (no extension): ").strip()
            if not directory or not name:
                print("ERROR: Directory and name must not be empty.")
                continue
            handle_create(['C', directory, '-n', name], admin=False)

        elif choice == 'o':
            filepath = input("  Enter full path to .dsu file: ").strip()
            if not filepath:
                print("ERROR: File path must not be empty.")
                continue
            handle_open(['O', filepath])

        elif choice == 'e':
            if current_profile is None:
                print("  No journal loaded. Use 'c' or 'o' first.")
                continue
            print("  Options: -usr  -pwd  -bio  -addpost  -delpost")
            cmd = input(
                "  Enter edit command (e.g. E -usr alice): "
            ).strip()
            if not cmd:
                print("ERROR: Command must not be empty.")
                continue
            try:
                tokens = shlex.split(cmd)
            except ValueError:
                print("ERROR: Could not parse command.")
                continue
            if tokens[0] != 'E':
                tokens = ['E'] + tokens
            handle_edit(tokens)

        elif choice == 'p':
            if current_profile is None:
                print("  No journal loaded. Use 'c' or 'o' first.")
                continue
            print("  Options: -usr  -pwd  -bio  -posts  -post ID  -all")
            cmd = input("  Enter print command (e.g. P -all): ").strip()
            if not cmd:
                print("ERROR: Command must not be empty.")
                continue
            try:
                tokens = shlex.split(cmd)
            except ValueError:
                print("ERROR: Could not parse command.")
                continue
            if tokens[0] != 'P':
                tokens = ['P'] + tokens
            handle_print(tokens)

        elif choice == 's':
            if current_profile is None:
                print("  No journal loaded. Use 'c' or 'o' first.")
                continue
            port_input = input(
                "  Enter DSP server port (default 3001): "
            ).strip()
            try:
                port = int(port_input) if port_input else 3001
            except ValueError:
                print("ERROR: Port must be a number.")
                continue
            handle_publish(port)

        elif choice == '':
            continue

        else:
            print("  Unknown option. Please choose from the menu above.")