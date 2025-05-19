import json

import argparse
from openai import OpenAI

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import file_parser

def build_prompt_function_localize(result, ):
    bug_information = (
        "Title: " + result['title'] + "\n" +
        "Description: " + result['description'] + "\n" +
        "Kernel Version: " + str(result['Kernel Version']) + "\n" +
        "Product: " + result['Product'] + "\n" +
        "Component: " + result['Component'] + "\n" +
        "Hardware: " + result['Hardware'] + "\n"
    )

    predict_files = result["reranked_files"]
    kernel_version = str(result['Kernel Version'])
    kernel_file_name = "linux-" + kernel_version + "/"
    kernel_path = os.path.join(kernel_path, kernel_file_name) 
    file_info_text = ""

    for i, candidate in enumerate(predict_files):
        file_content = file_parser.summary_file_by_Fline(kernel_path + candidate)
        if file_content is None:
            file_content = "The file may not exist in the kernel version."
        file_info_text += f"{i+1}. {candidate}\n Content summary: {file_content}\n\n"
    obtain_relevant_functions_and_vars_from_compressed_files_prompt_more = """
Please look through the following Linux Kernel Bug Report and the Skeleton of Relevant Files.
Identify all locations that need inspection or editing to fix the problem, including directly related areas as well as any potentially related global variables, constants, functions, and structures.
For each location you provide, either give the name of the structure, the name of a function, or the name of a global variable, or the name of a global constant.

### Linux Kernel Bug Report ###
{problem_statement}

### Skeleton of Relevant Files ###
{file_contents}

The returned locations should be separated by new lines ordered by most to least important.
Please return at most 10 locations.

### Examples:
```
file1.py function: my_function_1

file1.py structure: my_structure_1

file2.py variable: my_var

file3.py constant: my_con
file3.py function: my_function_2
```

Please return the locations in the same format as above.
Return just the locations wrapped with ```.
"""
    return obtain_relevant_functions_and_vars_from_compressed_files_prompt_more.format(problem_statement=bug_information, file_contents=file_info_text)

def get_openai_client(gpt_base_url, api_key):
    client = OpenAI(
        base_url=gpt_base_url,
        api_key=api_key,
    )
    return client

def process_func_predict(func_predict):
    func_predict = func_predict.split("\n")
    func_predict = [func.strip() for func in func_predict if func.strip()]
    return func_predict

def function_localize(data_path, save_path, gpt_base_url, api_key):
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    total_cost = 0.0

    results = utils.read_jsonl_data(data_path)
    client = get_openai_client(gpt_base_url, api_key)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        for i, result in enumerate(results):

            one_output_tokens = 0
            one_total_tokens = 0

            print(f"\rProcessing {i+1}/{len(results)} ({(i+1)/len(results)*100:.1f}%)", end="")
            content = build_prompt_function_localize(result=result)
            messages = [
                {"role": "system",
                 "content": "You are a linux kernel maintainer, skilled in analyzing the root cause of "
                            "kernel bugs and locating the related source code based on the given bug reports."},
                {"role": "user",
                 "content": content}
            ]
            completion_1 = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages,
                temperature=0.0
            )

            answer = completion_1.choices[0].message.content

            n_out_token = completion_1.usage.completion_tokens
            output_tokens += n_out_token
            used_tokens = completion_1.usage.total_tokens
            total_tokens += used_tokens
            one_output_tokens += n_out_token
            one_total_tokens += used_tokens
            print(answer)

            result['function_locations_raw'] = answer
            result['function_localize_output_tokens'] = one_output_tokens
            result['function_localize_total_tokens'] = one_total_tokens
            # Save result
            f.write(json.dumps(result) + "\n")
            input_tokens = total_tokens - output_tokens
            total_cost = input_tokens / 1000000 * 2.5 + output_tokens / 1000000 * 10
            print(f"Total tokens used: {total_tokens}")
            print(f"Input tokens used: {input_tokens}")
            print(f"Output tokens used: {output_tokens}")
            print(f"Total cost: ${total_cost}")

def main():
    parser = argparse.ArgumentParser(description="Function-level localization using LLMs for Linux kernel bugs.")
    parser.add_argument('--data_path', type=str, required=True, help='Path to the input JSONL data file')
    parser.add_argument('--save_path', type=str, required=True, help='Path to save the output JSONL file')
    parser.add_argument('--gpt_base_url', type=str, required=True, help='Base URL for GPT API')
    parser.add_argument('--api_key', type=str, required=True, help='API key for GPT API')
    parser.add_argument('--kernel_path', type=str, required=True, help='Path to the kernel source code directory')
    args = parser.parse_args()
    function_localize(
        data_path=args.data_path,
        save_path=args.save_path,
        gpt_base_url=args.gpt_base_url,
        api_key=args.api_key,
        kernel_path=args.kernel_path
    )

if __name__ == "__main__":
    main()