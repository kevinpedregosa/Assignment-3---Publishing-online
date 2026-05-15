# Kevin Noel Pedregosa
# pedregok@uci.edu
# 18447962

# a3.py
# Main entry file for the ICS 32 Assignment 3 Journal + DSP application.

import ui


def main():
    """Launch admin mode or friendly UI based on first user input."""
    print("Welcome to the ICS 32 Journal!")
    response = input(
        "Enter 'admin' for admin mode, or press Enter to continue: "
    ).strip()
    if response.lower() == 'admin':
        ui.run_admin()
    else:
        ui.run_ui()


if __name__ == "__main__":
    main()