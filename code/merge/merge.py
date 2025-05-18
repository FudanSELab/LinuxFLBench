# 合并三个排名的结果

import os
import json
import ast
import sys
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils



def combine_three_rankings(rank1, rank2, rank3, weight1=1/3, weight2=1/3, weight3=1/3):
    """
    Combine three ranking results, calculate weighted ranking and return the sorted result.
    Args:
        rank1, rank2, rank3: Three ranking lists
        weight1, weight2, weight3: Corresponding weights, default is 0.33 each, sum should be 1
    Returns:
        List of elements sorted by weighted ranking
    """
    # Ensure weights sum to 1
    if abs(weight1 + weight2 + weight3 - 1) > 0.001:
        print("Warning: The sum of weights is not 1, normalizing automatically.")
        total = weight1 + weight2 + weight3
        weight1 /= total
        weight2 /= total
        weight3 /= total
    # Create dicts to store the rank of each element
    rank_dict1 = {element: idx + 1 for idx, element in enumerate(rank1)}
    rank_dict2 = {element: idx + 1 for idx, element in enumerate(rank2)}
    rank_dict3 = {element: idx + 1 for idx, element in enumerate(rank3)}
    # Calculate weighted ranking
    weighted_ranks = {}
    for element in rank1:
        weighted_ranks[element] = 1 / rank_dict1[element] * weight1
    for element in rank2:
        if element not in weighted_ranks:
            weighted_ranks[element] = 1 / rank_dict2[element] * weight2
        else:
            weighted_ranks[element] += (1 / rank_dict2[element] * weight2)
    for element in rank3:
        if element not in weighted_ranks:
            weighted_ranks[element] = 1 / rank_dict3[element] * weight3
        else:
            weighted_ranks[element] += (1 / rank_dict3[element] * weight3)
    # Sort elements by weighted ranking
    sorted_elements = sorted(weighted_ranks.keys(), key=lambda x: weighted_ranks[x], reverse=True)
    return sorted_elements


def evaluate_three_rankings(path1, path2, path3, save_path, kernel_path, weights=[1/3, 1/3, 1/3]):
    """
    Evaluate the combined result of three rankings.
    Args:
        path1, path2, path3: Paths to three jsonl files containing rankings
        save_path: Path to save the merged result
        kernel_path: Root path to the Linux kernel source
        weights: List of three weights, default is 0.33 each
    """
    data1 = utils.read_jsonl_data(path1)
    data2 = utils.read_jsonl_data(path2)
    data3 = utils.read_jsonl_data(path3)
    predicts = []
    targets = []
    for i in range(min(len(data1), len(data2), len(data3))):
        kernel_version = str(data1[i]['Kernel Version'])
        kernel_file_name = "linux-" + kernel_version + "/"
        kernel_full_path = os.path.join(kernel_path, kernel_file_name)
        # Get original rankings
        rank1 = data1[i]['reranked_files']
        rank2 = data2[i]['reranked_files']
        rank3 = data3[i]['reranked_files']
        # Target file paths
        targets.append(data1[i]["paths"])
        # Combine three rankings
        combined_rank = combine_three_rankings(rank1, rank2, rank3, weights[0], weights[1], weights[2])
        combined_rank = utils.filter_non_exist_files(combined_rank, kernel_full_path)
        data1[i]['reranked_files'] = combined_rank
        predicts.append(combined_rank)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # Save merged data to new jsonl file
        with open(save_path, 'w') as f:
            for item in data1:
                f.write(json.dumps(item) + '\n')
    print(f"Number of evaluated samples: {len(predicts)}")
    print(f"Used weights: {weights}")
    # If evaluation_metrics is available, print metrics
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/eval")
        import evaluation_metrics
        print("Recall@1: ", evaluation_metrics.recall_at_k(targets, predicts, 1))
        print("Recall@5: ", evaluation_metrics.recall_at_k(targets, predicts, 5))
        print("Recall@10: ", evaluation_metrics.recall_at_k(targets, predicts, 10))
        print("MRR: ", evaluation_metrics.mean_reciprocal_rank(targets, predicts))
    except ImportError:
        print("evaluation_metrics module not found, skipping metric calculation.")


def main():
    parser = argparse.ArgumentParser(description="Merge and evaluate three ranking results.")
    parser.add_argument('--path1', type=str, required=True, help='Path to the first ranking jsonl file')
    parser.add_argument('--path2', type=str, required=True, help='Path to the second ranking jsonl file')
    parser.add_argument('--path3', type=str, required=True, help='Path to the third ranking jsonl file')
    parser.add_argument('--save_path', type=str, required=True, help='Path to save the merged result jsonl file')
    parser.add_argument('--kernel_path', type=str, required=True, help='Root path to the Linux kernel source')
    parser.add_argument('--weights', type=float, nargs=3, default=[1/3, 1/3, 1/3], help='Three weights for the rankings (default: 1/3 1/3 1/3)')
    args = parser.parse_args()
    evaluate_three_rankings(
        path1=args.path1,
        path2=args.path2,
        path3=args.path3,
        save_path=args.save_path,
        kernel_path=args.kernel_path,
        weights=args.weights
    )

if __name__ == "__main__":
    main()