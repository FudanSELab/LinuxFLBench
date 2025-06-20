import search_mails_bm25s

import time
import json
import os

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

def mail_retrival_test(data_path, save_path):
    start_time = time.time()
    results = utils.read_jsonl_data(data_path)
    count = 0

    
    for result in results:

        paths = result["paths"]
        predicts = result["predicts"]
        bug_date = result["Reported"]
        bug_summary = result["summary"]
        title = result["title"]
        description = result["description"]


        # query = title + description

        query = bug_summary

        search_mails_bm25s.directly_elasticSearch([query], 10, save_path, query_times=[bug_date])

        if paths[0] in predicts:
            count += 1
            
    end_time = time.time()
    print("count:")
    print(count/ len(results))
    print("Time taken:", end_time - start_time, "seconds")


RESULTS_PATH = "../../results/scaling_results/dir/agentless_with_bug_summary.jsonl"
MAIL_PATH = "../../results/mails/agentless_retrieval_with_bug_summary.jsonl"
mail_retrival_test(RESULTS_PATH, MAIL_PATH)
