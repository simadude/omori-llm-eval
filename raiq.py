import os
import json
import requests
import argparse
from dotenv import load_dotenv

def parse_questions_file(file_path):
    """Parse the .txt file to extract sections and question-answer pairs."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        sections = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("###"):
                section_name = line[3:].strip()
                current_section = {"section_name": section_name, "questions": []}
                sections.append(current_section)
                i += 1
            elif line.startswith("Q:"):
                question = line[2:].strip()
                i += 1
                if i < len(lines) and lines[i].strip().startswith("A:"):
                    answer = lines[i][2:].strip()
                    current_section["questions"].append({"question": question, "expected_answer": answer})
                    i += 1
                else:
                    raise ValueError(f"Expected 'A:' after 'Q:' at line {i}")
            else:
                i += 1
        return sections
    except Exception as e:
        print(f"Error parsing questions file: {e}")
        return []

def get_llm_reply(model, question, api_key):
    """Send a question to the OpenRouter LLM using the Chat Completions API."""
    url = "https://openrouter.ai/api/v1/chat/completions"  # Confirm this endpoint
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    system_prompt = (
        "You're an expert in the indie horror game OMORI. "
        "The question below was asked by a human. Be careful, as it could be a nonsensical question."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,  # Adjust as needed
        "temperature": 0.1  # Adjust as needed
    }
    reply = ""
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
    except KeyError:
        print("Unexpected response format from the API")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return reply

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Send questions to an LLM and save results to JSON")
    parser.add_argument("--model", required=True, help="OR model name (e.g., 'provider/model-v1.4')")
    parser.add_argument("--input", required=True, help="Path to the input .txt file")
    parser.add_argument("--output", required=True, help="Path to the output JSON file")
    args = parser.parse_args()
    
    model = args.model
    input_file = args.input
    output_file = args.output
    
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise ValueError("Please set the OPENROUTER_KEY environment variable in your .env file.")
    
    # Parse questions and get LLM replies
    sections = parse_questions_file(input_file)
    if not sections:
        print("No sections found. Exiting.")
        return

    # Calculate total number of questions
    total_questions = sum(len(section["questions"]) for section in sections)
    print(f"Total Questions: {total_questions}")

    completed_questions = 0
    current_section_name = None  # Track the current section name

    for section in sections:
        section_name = section["section_name"]

        # Output section change message
        if current_section_name is None:
            print(f"SECTION: {section_name}")
        else:
            print(f"NEXT SECTION: {section_name}")

        current_section_name = section_name  # Update the current section name

        for question in section["questions"]:
            reply = get_llm_reply(model, question["question"], api_key)
            completed_questions += 1
            print(f"Processed Question {completed_questions} / {total_questions}")
            question["reply"] = reply
            question["correct"] = None  # Set to null as required
    
    # Save results to JSON
    result = {"model": model, "sections": sections}
    try:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=4)
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Failed to write results to file: {e}")

if __name__ == "__main__":
    main()