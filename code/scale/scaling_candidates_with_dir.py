from openai import OpenAI
import json
import argparse

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils


def up_scale_by_dir(kernel_version, predicts, kernel_path):
    # Expand the predicted file paths to all files in their directories
    kernel_file_name = "linux-" + kernel_version + "/"
    kernel_path = os.path.join(kernel_path, kernel_file_name)

    predict_dirs = []
    for file in predicts:
        last_slash_index = file.rfind('/')
        predict_dirs.append(file[:last_slash_index + 1])

    predict_dirs = utils.deduplicate(predict_dirs)

    print("predict_dirs:")
    print(predict_dirs)

    rerank_file_list = []
    return_string = ""

    for directory in predict_dirs:
        absolute_dir_path = os.path.join(kernel_path, directory)

        if not os.path.exists(absolute_dir_path):
            continue
        files = os.listdir(absolute_dir_path)
        c_h_files = [os.path.join(directory, file) for file in files if file.endswith('.c') or file.endswith('.h')]
        return_string += "\n" + directory + "\n"
        return_string += "\n".join(c_h_files)

        rerank_file_list.extend(c_h_files)
    
    rerank_file_list = utils.deduplicate(rerank_file_list)
    
    return return_string
    # return rerank_file_list




def build_prompt_scale_by_dir(result, kernel_path):
    kernel_version = result['Kernel Version']
    predicts = result["predicts"]
    reranked_files = up_scale_by_dir(kernel_version, predicts, kernel_path)
    
    bug_information = ("Title: " + result['title'] + "\n" +
                        "Description: " + result['description'] + "\n" +
                        "Kernel Version: " + str(result['Kernel Version']) + "\n" +
                        "Product: " + result['Product'] + "\n" +
                        "Component: " + result['Component'] + "\n" +
                        "Hardware: " + result['Hardware'] + "\n")
    
    bug_prompt = f"""Please look through the following Linux kernel bug report and candidate files, and select a list of files that one would need to edit to fix the bug.
Here is the information about the bug:
### Linux kernel bug report ###
{bug_information}
###

Based on the bug provided above, I will present a list of candidate files that may be relevant to the bug.
### candidate files ###
{reranked_files}
###

Please select files that are most likely to need modification to fix this bug.

Your response should be in the format of a list of file paths, and should be ordered by relevance in descending order.
Please return at most 10 files, at least 1 file, and do not include the directories.
Please ensure that your answer is in the list format without any additional commentary.

### output example ###
['net/ipv6/proc.c', 'net/ipv6/netfilter/ip6_tables.c']
###

Please format your response strictly according to the format provided above without commentary.
"""
    return bug_prompt


def candidates_filter_once(data_path, save_path, gpt_base_url, api_key, kernel_path):
    # Filter candidates using GPT model and save the results
    results = utils.read_jsonl_data(data_path)

    input_tokens = 0
    output_tokens = 0
    total_tokens  = 0
    total_cost = 0.0

    client = OpenAI(
        base_url=gpt_base_url,
        api_key=api_key
    )

    with open(save_path, 'w') as f:
        for result in results:
            predicts = result["predicts"]
            if len(predicts) == 0:
                result['reranked_files'] = []
                # Save result
                f.write(json.dumps(result) + "\n")
                continue

            bug_prompt = build_prompt_scale_by_dir(result, kernel_path)

            messages = [
                {"role": "system",
                    "content": "You are a linux kernel maintainer, skilled in analyzing the root cause of "
                            "kernel bugs and locating the related source code files based on the given bug reports."},
                {"role": "user",
                "content": bug_prompt},
            ]
            
            completion = client.chat.completions.create(
                model = "gpt-4o-2024-08-06",
                messages = messages,
                temperature = 0
                )
        
            relavance_answer = completion.choices[0].message.content
            relavance_file_list = utils.formate_predicts(relavance_answer)
        
            print(relavance_answer)

            one_out_tokens = completion.usage.completion_tokens
            output_tokens += one_out_tokens
            
            one_used_tokens = completion.usage.total_tokens
            total_tokens += one_used_tokens

            input_tokens = total_tokens - output_tokens       
            total_cost = input_tokens / 1000000 * 2.5 + output_tokens / 1000000 * 10
            
            print(f"Total tokens used: {total_tokens}")
            print(f"Input tokens used: {input_tokens}")
            print(f"Output tokens used: {output_tokens}")
            print(f"Total cost: ${total_cost}")
            print("---------------------------------------------------")

            result['reranked_files'] = relavance_file_list
            result['input_tokens'] = one_used_tokens - one_out_tokens
            result['output_tokens'] = one_out_tokens
            # Save result
            f.write(json.dumps(result) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Filter and rerank Linux kernel bug candidate files using GPT.")
    parser.add_argument('--data_path', type=str, required=True, help='Path to the input JSONL data file')
    parser.add_argument('--save_path', type=str, required=True, help='Path to save the output JSONL file')
    parser.add_argument('--gpt_base_url', type=str, required=True, help='Base URL for GPT API')
    parser.add_argument('--api_key', type=str, required=True, help='API key for GPT API')
    parser.add_argument('--kernel_path', type=str, required=True, help='Root path to the Linux kernel source')
    args = parser.parse_args()

    candidates_filter_once(
        data_path=args.data_path,
        save_path=args.save_path,
        gpt_base_url=args.gpt_base_url,
        api_key=args.api_key,
        kernel_path=args.kernel_path
    )

if __name__ == "__main__":
    main()

