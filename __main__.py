import os
import fnmatch
import tiktoken
import click
from typing import List
from pydantic import BaseModel
from openai import OpenAI

MODEL_NAME = os.environ['MODEL_NAME']
PRICE_PER_TOKEN = float(os.environ['PRICE_PER_TOKEN'])

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

class Review(BaseModel):
    filename: str
    issue_severity: str
    issue_type: str
    description: str

class Reviews(BaseModel):
    reviews: List[Review]

def get_ignore_patterns():
    with open('./ignore_file_patterns.txt', 'r') as f:
        return f.read().splitlines()
    
def get_context_patterns():
    with open('./context_file_patterns.txt', 'r') as f:
        return f.read().splitlines()
    
def get_file_source_template():
    with open('./prompt_templates/file_source.txt', 'r') as f:
        return f.read()
    
def get_homework_context_template():
    with open('./prompt_templates/homework_context.txt', 'r') as f:
        return f.read()
    
def get_output_report_template():
    with open('./output_templates/report.md', 'r') as f:
        return f.read()
    
def get_output_result_entry_template():
    with open('./output_templates/result_entry.md', 'r') as f:
        return f.read()

def get_file_list(directory, context_patterns, ignore_patterns):
    files = []

    for dirpath, _, filenames in os.walk(directory):
        parsed_filenames = []

        for file in filenames:
            if not any(fnmatch.fnmatch(file, pattern) for pattern in ignore_patterns) and any(fnmatch.fnmatch(file, pattern) for pattern in context_patterns):
                parsed_filenames.append(file.replace(directory, ''))
        
        for filename in parsed_filenames:
            files.append(os.path.join(dirpath, filename))
    
    return files

def main():
    files = get_file_list('./homework_source_code', get_context_patterns(), get_ignore_patterns())

    if (len(files) == 0):
        click.echo("No files found in directory")
        exit()
    
    # Read all filtered files into array
    file_contents = []

    for file in files:
        with open(file, 'r') as f:
            file_contents.append((file, f.read()))

    
    # Concatenate all files into one string
    file_contents_string = ""
    file_contents_string_array = []
    content_template = get_file_source_template()

    for file, content in file_contents:
        formatted_content = content_template.format(filename=file, source_code=content)
        file_contents_string += content_template.format(filename=file, source_code=content)
        file_contents_string_array.append(formatted_content)

    # Get homework context
    homework_context = get_homework_context_template()

    # Calculate price
    encoder = tiktoken.encoding_for_model(MODEL_NAME)
    token_count = len(encoder.encode(homework_context + file_contents_string))

    click.echo("Token count: " + str(token_count))
    click.echo("Input prompt cost: $" + str(token_count * PRICE_PER_TOKEN))
    click.confirm('Do you want to continue?', abort=True, default=True)

    messages = [{
        "role": "system",
        "content": homework_context
    }]
    messages.extend([{
        "role": "user",
        "content": file_content
    } for file_content in file_contents_string_array])

    # Send prompt to OpenAI
    completion = client.beta.chat.completions.parse(
        model=MODEL_NAME,
        messages=messages,
        response_format=Reviews,
    )

    review_list = completion.choices[0].message.parsed.reviews
    minor_issues = []
    major_issues = []
    critical_issues = []

    for review in review_list:
        lowercase_severity = review.issue_severity.lower()
        if lowercase_severity == 'minor':
            minor_issues.append(review)
        elif lowercase_severity == 'major':
            major_issues.append(review)
        elif lowercase_severity == 'critical':
            critical_issues.append(review)

    # Format output and write response to file
    with open('./result.md', 'w') as f:
        output_report_template = get_output_report_template()
        result_entry_template = get_output_result_entry_template()

        entry_string = ""

        for review in critical_issues + major_issues + minor_issues:
            entry_string += result_entry_template.format(
                issue_severity=review.issue_severity,
                filename=review.filename,
                issue_type=review.issue_type,
                description=review.description
            )
            entry_string += "\n"

        f.write(output_report_template.format(
            result_entries=entry_string,
            critical_issue_count=str(len(critical_issues)),
            major_issue_count=str(len(major_issues)),
            minor_issue_count=str(len(minor_issues))
        ))

        print("Output written to result.md")


if __name__ == "__main__":
    main()
