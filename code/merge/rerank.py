import argparse
from openai import OpenAI
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils


def build_prompt_rerank_base(result):
    bug_information = (
        "Title: " + result['title'] + "\n" +
        "Description: " + result['description'] + "\n" +
        "Kernel Version: " + str(result['Kernel Version']) + "\n" +
        "Product: " + result['Product'] + "\n" +
        "Component: " + result['Component'] + "\n" +
        "Hardware: " + result['Hardware'] + "\n"
    )
    predict_files = result["reranked_files"]
    file_list = '[' + ', '.join(predict_files) + ']'
    # Build prompt
    prompt = f"""Please carefully analyze the following Linux kernel bug report, and identify which code file might contain the bug.
The information of the Linux kernel bug is as follows:
### Linux kernel bug report ###
{bug_information}
###

Below is a list of candidate files that might contain this bug:
### Candidate files ###
{file_list}
###

Please rerank these files based on the bug information, placing the most likely file containing the bug or needing modification to fix the bug at the top. Your result must include all candidate files.
### Note: ###
1. Your result must include all candidate files. Do not add or remove files from the list.
2. Your answer should strictly follow this format: ['net/ipv6/proc.c', 'net/ipv6/ipv6_sockglue.c'], where all elements are strings.
Provide only the reordered list as requested, without adding any comments or additional information.
"""
    return prompt


def parse_model_response(response, candidate_files):
    """
    Parse the model response to extract the reranked file list
    Parameters:
    response: The model-generated response text
    candidate_files: The original list of candidate files (to ensure all files are included)
    Returns:
    The reranked list of files
    """
    if not response:
        return candidate_files
    reranked_files = []
    for line in response.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split(". ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            file_path = parts[1].strip()
            if file_path in candidate_files and file_path not in reranked_files:
                reranked_files.append(file_path)
        elif line in candidate_files and line not in reranked_files:
            reranked_files.append(line)
    for file in candidate_files:
        if file not in reranked_files:
            reranked_files.append(file)
    return reranked_files


def rerank_base(data_path, save_path, gpt_base_url, api_key):
    """
    Rerank candidate files for each bug report using GPT model and save the results.
    """
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    total_cost = 0.0
    results = utils.read_jsonl_data(data_path)
    client = OpenAI(
        base_url=gpt_base_url,
        api_key=api_key
    )
    with open(save_path, 'w') as f:
        for i, result in enumerate(results):
            print(f"\rProcessing {i+1}/{len(results)} ({(i+1)/len(results)*100:.1f}%)", end="")

            predict_files = result["reranked_files"]


            if len(predict_files) < 2:
                print("The number of candidate files is less than 2, skipping...")
                result['rerank_output_tokens'] = 0
                result['rerank_total_tokens'] = 0
                f.write(json.dumps(result)+'\n')
                continue

            one_output_tokens = 0
            one_total_tokens = 0

            rerank_prompt = build_prompt_rerank_base(result)

            print("*"*80)
            print(rerank_prompt)
            messages = [
                {"role": "system",
                 "content": "You are a linux kernel maintainer, skilled in analyzing the root cause of "
                            "kernel bugs and locating the related source code files based on the given bug reports."},
                {"role": "user",
                 "content": rerank_prompt}
            ]

            completion_1 = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages,
                temperature=0.0
            )
            answer = completion_1.choices[0].message.content

            print("*"*80)
            print(answer)

            n_out_token = completion_1.usage.completion_tokens
            output_tokens += n_out_token
            used_tokens = completion_1.usage.total_tokens
            total_tokens += used_tokens
            one_output_tokens += n_out_token
            one_total_tokens += used_tokens

            reranked_files = utils.formate_predicts(answer, result['reranked_files'])

            result['reranked_files'] = reranked_files
            print(reranked_files)
            result['rerank_output_tokens'] = one_output_tokens
            result['rerank_total_tokens'] = one_total_tokens

            # Save result
            f.write(json.dumps(result) + "\n")
            input_tokens = total_tokens - output_tokens
            total_cost = input_tokens / 1000000 * 2.5 + output_tokens / 1000000 * 10
            print(f"Total tokens used: {total_tokens}")
            print(f"Input tokens used: {input_tokens}")
            print(f"Output tokens used: {output_tokens}")
            print(f"Total cost: ${total_cost}")

def main():
    parser = argparse.ArgumentParser(description="Rerank Linux kernel candidate files using GPT.")
    parser.add_argument('--data_path', type=str, required=True, help='Path to the input JSONL data file')
    parser.add_argument('--save_path', type=str, required=True, help='Path to save the output JSONL file')
    parser.add_argument('--gpt_base_url', type=str, required=True, help='Base URL for GPT API')
    parser.add_argument('--api_key', type=str, required=True, help='API key for GPT API')
    args = parser.parse_args()
    rerank_base(
        data_path=args.data_path,
        save_path=args.save_path,
        gpt_base_url=args.gpt_base_url,
        api_key=args.api_key
    )

if __name__ == "__main__":
    main()



