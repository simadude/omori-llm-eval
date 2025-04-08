import os
import json
import matplotlib.pyplot as plt
import numpy as np
import re # For cleaning up names potentially

# --- Configuration ---
# <<< CHANGE THIS >>> Set the path to the folder containing your JSON files
JSON_FOLDER_PATH = './rated-replies'
# <<< CHANGE THIS (Optional) >>> Set the desired output filename for the plot
OUTPUT_FILENAME = 'llm_performance_comparison.png'
# Sections found in JSONs but not listed here will be added alphabetically at the end.
SECTION_ORDER = ["EASY", "NORMAL", "HARD", "VERY HARD"]
# --- End Configuration ---

def clean_name(name):
    """Removes potentially problematic characters for display."""
    # Example: remove provider prefix if present like 'provider/'
    name = re.sub(r'^[a-zA-Z0-9_-]+/', '', name)
    # Example: remove tags like ':experimental'
    name = re.sub(r':.*', '', name)
    return name.strip()

def calculate_scores(filepath):
    """
    Reads a JSON file and calculates the percentage of correct answers per section.

    Args:
        filepath (str): The path to the JSON file.

    Returns:
        tuple: (model_name, section_scores) or (None, None) if error.
               section_scores is a dictionary {section_name: percentage_correct}.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        model_name = data.get('model', 'Unknown Model')
        sections_data = data.get('sections', [])
        section_scores = {}

        if not sections_data:
            print(f"Warning: No sections found in {filepath}")
            return model_name, {}

        for section in sections_data:
            section_name = section.get('section_name', 'Unnamed Section')
            questions = section.get('questions', [])

            if not questions:
                # Handle sections with no questions if necessary (e.g., assign 0% or skip)
                section_scores[section_name] = 0.0
                print(f"Warning: No questions found in section '{section_name}' in file {filepath}")
                continue

            correct_count = 0
            total_count = len(questions)

            for question in questions:
                # Check explicitly for True, as 'correct' could be other things
                if question.get('correct') is True:
                    correct_count += 1

            percentage = (correct_count / total_count) * 100 if total_count > 0 else 0.0
            section_scores[section_name] = percentage

        return model_name, section_scores

    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from - {filepath}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred while processing {filepath}: {e}")
        return None, None

def plot_results(all_results, section_order, output_filename):
    """
    Generates and saves a grouped bar chart of the LLM performance,
    ordering sections based on the provided list.

    Args:
        all_results (dict): {model_name: {section_name: score}}.
        section_order (list): The desired order of section names for the x-axis.
        output_filename (str): The name for the output PNG file.
    """
    if not all_results:
        print("No results to plot.")
        return

    # --- Data Preparation for Plotting ---
    models = list(all_results.keys())
    model_display_names = {m: clean_name(m) for m in models}

    # Gather all unique section names across all models
    all_section_names_from_data = set()
    for sections in all_results.values():
        all_section_names_from_data.update(sections.keys())

    # --- Custom Sorting Logic ---
    sorted_section_names = []
    remaining_sections = set(all_section_names_from_data) # Start with all found sections

    # Add sections based on the defined order first
    for section_name in section_order:
        if section_name in remaining_sections:
            sorted_section_names.append(section_name)
            remaining_sections.remove(section_name) # Remove it so it's not added again

    # Add any remaining sections (not in section_order) alphabetically at the end
    if remaining_sections:
        print(f"Note: Sections not in defined SECTION_ORDER found: {', '.join(sorted(list(remaining_sections)))}. Adding them to the end of the plot.")
        sorted_section_names.extend(sorted(list(remaining_sections)))
    # --- End Custom Sorting Logic ---


    if not sorted_section_names:
        print("No sections found across all files to plot.")
        return

    # Prepare data for plotting (same as before, but using the new sorted_section_names)
    scores_by_model = {model: [] for model in models}
    for model in models:
        for section_name in sorted_section_names:
            score = all_results[model].get(section_name, 0.0)
            scores_by_model[model].append(score)

    # --- Plotting (Mostly unchanged from before) ---
    num_sections = len(sorted_section_names)
    num_models = len(models)
    x = np.arange(num_sections)
    width = 0.8 / num_models
    group_offset = (1 - num_models) * width / 2

    fig, ax = plt.subplots(figsize=(max(10, num_sections * 1.5), 6))

    for i, model in enumerate(models):
        offset = group_offset + i * width
        rects = ax.bar(x + offset, scores_by_model[model], width, label=model_display_names[model])
        # Optional: ax.bar_label(rects, padding=3, fmt='%.1f')

    ax.set_ylabel('Результативность (%)')
    ax.set_title('Результативность Больших Языковых Моделей')
    ax.set_xticks(x, sorted_section_names) # Use the correctly ordered section names
    ax.legend(title="Использованные БЯМ", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()

    # --- Save Plot ---
    try:
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved successfully to: {output_filename}")
    except Exception as e:
        print(f"\nError saving plot: {e}")

    # Optional: plt.show()


# --- Main Execution ---
if __name__ == "__main__":
    all_model_results = {}
    print(f"Scanning for JSON files in: {os.path.abspath(JSON_FOLDER_PATH)}")

    if not os.path.isdir(JSON_FOLDER_PATH):
        print(f"Error: Folder not found - {JSON_FOLDER_PATH}")
    else:
        found_files = False
        for filename in os.listdir(JSON_FOLDER_PATH):
            if filename.lower().endswith('.json'):
                found_files = True
                filepath = os.path.join(JSON_FOLDER_PATH, filename)
                print(f"Processing: {filename}...")
                model_name, section_scores = calculate_scores(filepath)

                if model_name is not None and section_scores is not None:
                    # Handle potential duplicate model names if needed (e.g., append count)
                    if model_name in all_model_results:
                         print(f"Warning: Duplicate model name '{model_name}' found in {filename}. Overwriting previous results for this model.")
                    if section_scores: # Only add if there are actual scores
                        all_model_results[model_name] = section_scores
                    else:
                        print(f"Skipping model '{model_name}' from {filename} due to no valid section data.")

        if not found_files:
             print("No JSON files found in the specified folder.")
        elif not all_model_results:
            print("No valid model results were extracted from the JSON files.")
        else:
            # Generate the plot
            plot_results(all_model_results, SECTION_ORDER, OUTPUT_FILENAME)