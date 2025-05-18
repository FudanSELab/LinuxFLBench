import argparse
import os
from openai import OpenAI
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

def build_prompt_scale_by_guess(result, mail_content):
    bug_information = ("Title: " + result['title'] + "\n" +
            "Description: " + result['description'] + "\n" +
            "Kernel Version: " + str(result['Kernel Version']) + "\n" +
            "Product: " + result['Product'] + "\n" +
            "Component: " + result['Component'] + "\n" +
            "Hardware: " + result['Hardware'] + "\n")



    if mail_content:
        mail_prompt = f"""
To assist in your analysis, here are some emails retrieved using BM25 that may be relevant to the bug. Use them to inspire and identify additional possible causes:
### Mails ###  
{mail_content}  
###
"""
    else:
        mail_prompt = ''

    bug_prompt = f"""Please review the following Linux kernel bug report, and then deduce the possible causes of the bug and provide corresponding code files and a potential fix. 
The bug is known to be related to the kernel code, and the fix should involve modifications to kernel code files.
Here is the information about the bug:
### Linux kernel bug report ###
{bug_information}
###
{mail_prompt}
Based on the information provided above, please output the possible causes, relevant code files, and solutions. Your response should follow the format below.
### Output format ###
[
{{
'cause': 'A description of the potential cause of the bug.',
'code_file': 'Path of the code file that is most likely related to the bug.',
'fix_solution': 'A short description of the fix solution to apply in the code file.'
}},
...
]

Please ensure the following:
- List as many causes as possible, ordered by relevance in descending order, with the most likely cause first.
- For each cause, list all relevant code files and their corresponding fixes, but only provide one code file and one fix per entry.
- The relevant code file is not necessarily the one causing the bug but should be a file where the bug can be fixed.
- The code file should be in the format of "net/ipv6/proc.c".
- Format your response strictly according to the format provided above without commentary.
"""
    return bug_prompt


def candidates_scale_by_guess(data_path, save_path, gpt_base_url, api_key, mail_path=None):
    """
    Use GPT to analyze bug reports, optionally with related emails, deduce possible causes, relevant code files, and solutions, and save the results.
    """
    results = utils.read_jsonl_data(data_path)
    mails_all = utils.read_jsonl_data(mail_path) if mail_path else None

    input_tokens = 0
    output_tokens = 0
    total_tokens  = 0
    total_cost = 0.0

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    client = OpenAI(
        base_url=gpt_base_url,
        api_key=api_key
    )

    with open(save_path, 'w') as f:
        for idx, result in enumerate(results):
            bug_id = result['id']
            print(f"---------------Processing bug {idx+1}/{len(results)}, ID: {bug_id}---------------")


            mail_content = ''
            if mails_all:
                mails = mails_all[idx]['email_content']
                new_mails = []
                for m in mails:
                    mail_files = utils.extract_filepath(m)
                    if len(mail_files) < 8 and len(mail_files) > 0:
                        new_mails.append(m)
                for i in range(len(new_mails)):
                    mail = new_mails[i]
                    mail_content += f"mail {i+1}: {mail}\n"
                if len(mail_content) > 30000:
                    mail_content = mail_content[:30000]

            bug_prompt = build_prompt_scale_by_guess(result, mail_content)

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
            possible_causes = utils.formate_predicts(relavance_answer)
        
            print(possible_causes)

            relavance_file_list = []
            for cause in possible_causes:
                relavance_file_list.append(cause['code_file'])
            relavance_file_list = utils.deduplicate(relavance_file_list)

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

            result['causes'] = possible_causes
            result['reranked_files'] = relavance_file_list
            result['input_tokens'] = one_used_tokens - one_out_tokens
            result['output_tokens'] = one_out_tokens
            # Save result
            f.write(json.dumps(result) + "\n")

def main():
    parser = argparse.ArgumentParser(description="Filter and rerank Linux kernel bug candidate files using GPT and related emails.")
    parser.add_argument('--data_path', type=str, required=True, help='Path to the input JSONL data file')
    parser.add_argument('--save_path', type=str, required=True, help='Path to save the output JSONL file')
    parser.add_argument('--gpt_base_url', type=str, required=True, help='Base URL for GPT API')
    parser.add_argument('--api_key', type=str, required=True, help='API key for GPT API')
    parser.add_argument('--mail_path', type=str, required=False, help='Path to the related mail JSONL file (optional)')
    args = parser.parse_args()

    candidates_scale_by_guess(
        data_path=args.data_path,
        save_path=args.save_path,
        gpt_base_url=args.gpt_base_url,
        api_key=args.api_key,
        mail_path=args.mail_path
    )

if __name__ == "__main__":
    main()