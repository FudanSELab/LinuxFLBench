import ast
import argparse

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

import evaluation_metrics


def evaluate_valid(path):
    data = utils.read_jsonl_data(path)
    predicts = []
    targets = []
    for index, result in enumerate(data):
        targets.append(result["paths"])
        if "reranked_files" not in result:
            reranked_files = result['predicts']
        else:
            reranked_files = result['reranked_files']
        if isinstance(reranked_files, str):
            reranked_files = "[" + reranked_files.split("[")[1].split("]")[0] + "]"
            reranked_files = ast.literal_eval(reranked_files)
        predicts.append(reranked_files)
    print(f"Number of predictions: {len(predicts)}")
    print("Recall@1: ", evaluation_metrics.recall_at_k(targets, predicts, 1))
    print("Recall@5: ", evaluation_metrics.recall_at_k(targets, predicts, 5))
    print("Recall@10: ", evaluation_metrics.recall_at_k(targets, predicts, 10))
    print("MRR: ", evaluation_metrics.mean_reciprocal_rank(targets, predicts))


def main():
    parser = argparse.ArgumentParser(description="Evaluate three ranking results.")
    parser.add_argument('--path', type=str, required=True, help='Path to the ranking jsonl file')
    args = parser.parse_args()
    print("Evaluating path:", args.path)
    evaluate_valid(args.path)


if __name__ == "__main__":
    main()