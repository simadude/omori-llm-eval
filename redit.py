import json
import argparse
import os
import sys

def load_json(filepath):
    """Loads JSON data from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at '{filepath}'")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. Check file format.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading the file: {e}")
        return None

def save_json(filepath, data):
    """Saves Python data to a JSON file."""
    try:
        # Create a backup before overwriting
        backup_path = filepath + ".bak"
        if os.path.exists(filepath):
             try:
                 # Attempt to remove old backup first if it exists
                 if os.path.exists(backup_path):
                     os.remove(backup_path)
                 os.rename(filepath, backup_path)
                 print(f"Backup of previous version created at '{backup_path}'")
             except OSError as backup_e:
                 print(f"Warning: Could not create backup: {backup_e}")


        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4) # Use indent for pretty printing
        print(f"Successfully saved changes to '{filepath}'")
        # Optionally remove backup after successful save
        # if os.path.exists(backup_path):
        #    os.remove(backup_path)
        return True
    except IOError as e:
        print(f"Error: Could not write to file '{filepath}'. {e}")
        # Attempt to restore backup if save failed and backup exists
        if os.path.exists(backup_path) and not os.path.exists(filepath):
             try:
                 os.rename(backup_path, filepath)
                 print("Restored from backup due to save error.")
             except Exception as restore_e:
                 print(f"Error: Could not restore backup after failed save: {restore_e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while saving the file: {e}")
        return False

def check_section_completeness(section):
    """Checks if any question in the section has correct=None."""
    if "questions" not in section:
        return True # No questions, so technically complete
    for question in section.get("questions", []):
        if question.get("correct") is None:
            return False # Found at least one null
    return True # All questions have a non-null 'correct' status

def display_main_menu(data):
    """Displays the main menu listing sections and their status."""
    print("\n--- JSON Editor Main Menu ---")
    if not data or "sections" not in data:
        print("No sections found in the JSON data.")
        return

    sections = data.get("sections", [])
    if not sections:
        print("The 'sections' list is empty.")
        return

    print("Sections:")
    for i, section in enumerate(sections):
        section_name = section.get("section_name", f"Unnamed Section {i+1}")
        is_complete = check_section_completeness(section)
        indicator = "" if is_complete else " (!)" # Add indicator if incomplete
        print(f"  {i+1}: {section_name}{indicator}")

    print("\nOptions:")
    print("  Enter section number to view/edit.")
    print("  s: Save changes and exit")
    print("  q: Quit without saving")
    print("-----------------------------")

def display_section_menu(section_data, section_index):
    """Displays the questions within a selected section."""
    section_name = section_data.get("section_name", f"Unnamed Section {section_index + 1}")
    print(f"\n--- Editing Section: {section_name} ---")

    questions = section_data.get("questions", [])
    if not questions:
        print("This section has no questions.")
    else:
        print("Questions:")
        for i, q in enumerate(questions):
            current_status = q.get('correct')
            status_str = 'None' if current_status is None else str(current_status)
            print(f"  {i+1}: {q.get('question', 'N/A')} (Correct: {status_str})")

    print("\nOptions:")
    print("  Enter question number to start editing sequence from there.")
    print("  b: Back to main menu")
    print("--------------------------------------")

def edit_question_correct_status(question, question_num, total_questions):
    """Allows editing the 'correct' status of a single question. Returns False if user cancels."""
    print(f"\n--- Edit Question ({question_num}/{total_questions}) ---")
    print(f"  Question:        {question.get('question', 'N/A')}")
    print(f"  Expected Answer: {question.get('expected_answer', 'N/A')}")
    print(f"  Reply:           {question.get('reply', 'N/A')}")
    current_status = question.get('correct')
    status_str = 'None' if current_status is None else str(current_status)
    print(f"  Current Status:  {status_str}")
    print("---------------------------" + "-"*len(str(question_num) + str(total_questions))) # Dynamic separator

    while True:
        choice = input("Is the reply correct? (y/n/c - yes/no/cancel sequence): ").lower().strip()
        if choice == 'y':
            question['correct'] = True
            print("Status set to True.")
            return True # Continue sequence
        elif choice == 'n':
            question['correct'] = False
            print("Status set to False.")
            return True # Continue sequence
        elif choice == 'c':
            print("Edit sequence cancelled.")
            return False # Stop sequence
        else:
            print("Invalid input. Please enter 'y', 'n', or 'c'.")


def main():
    """Main function to run the CLI."""
    parser = argparse.ArgumentParser(description="CLI tool to edit 'correct' status in specific JSON files.")
    parser.add_argument("filepath", help="Path to the JSON file to edit.")
    args = parser.parse_args()

    data = load_json(args.filepath)
    if data is None:
        sys.exit(1) # Exit if file loading failed

    print(f"Loaded '{args.filepath}'. Starting editor...") # Generic welcome

    while True:
        display_main_menu(data)
        choice = input("Enter choice: ").lower().strip()

        if choice == 'q':
            # Optional: Add a confirmation step if changes were made
            print("Exiting without saving.")
            break
        elif choice == 's':
            if save_json(args.filepath, data):
                print("Changes saved. Exiting.")
            else:
                print("Save failed. Please check errors above. Not exiting.")
                # Stay in the loop to allow user to retry save or quit
                continue # Go back to main menu
            break # Exit after successful save
        elif choice.isdigit():
            try:
                section_idx = int(choice) - 1
                sections = data.get("sections", [])
                if 0 <= section_idx < len(sections):
                    # --- Section Editing Loop ---
                    while True:
                        current_section = sections[section_idx]
                        display_section_menu(current_section, section_idx)
                        section_choice = input("Enter choice: ").lower().strip()

                        if section_choice == 'b':
                            print("Returning to main menu.")
                            break # Go back to main menu
                        elif section_choice.isdigit():
                            try:
                                start_question_idx = int(section_choice) - 1
                                questions = current_section.get("questions", [])
                                total_q = len(questions)

                                if 0 <= start_question_idx < total_q:
                                    # --- Sequential Editing Starts Here ---
                                    print(f"\nStarting edit sequence from question {start_question_idx + 1}...")
                                    for current_q_idx in range(start_question_idx, total_q):
                                        question_to_edit = questions[current_q_idx]
                                        # Pass current and total question numbers for context
                                        proceed = edit_question_correct_status(question_to_edit, current_q_idx + 1, total_q)
                                        if not proceed: # User entered 'c' to cancel
                                            break # Exit the inner for loop
                                    # --- Sequential Editing Ends Here ---
                                    # After loop finishes (or breaks), we automatically fall back
                                    # to the section menu display in the next iteration of the
                                    # "while True" section loop.
                                else:
                                    print("Invalid question number.")
                            except ValueError:
                                print("Invalid input. Please enter a number or 'b'.")
                        else:
                            print("Invalid input. Please enter a question number or 'b'.")
                    # --- End Section Editing Loop ---
                else:
                    print("Invalid section number.")
            except ValueError:
                print("Invalid input. Please enter a number, 's', or 'q'.")
        else:
            print("Invalid input. Please enter a section number, 's', or 'q'.")

    print("\nEditor closed.") # Generic closing


if __name__ == "__main__":
    main()