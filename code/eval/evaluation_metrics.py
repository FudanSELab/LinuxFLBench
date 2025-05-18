def precision(actual, predicted):
    if len(predicted) == 0:
        return 0

    actual_set = set(actual)
    correct = len(actual_set.intersection(predicted))
    return correct / len(predicted)


def precision_at_k(actual_list, predicted_list, k):
    return sum(precision(actual, predicted[:k]) for actual, predicted in zip(actual_list, predicted_list)) / len(
        actual_list)


def recall(actual, predicted):
    if len(predicted) == 0:
        return 0

    actual_set = set(actual)
    correct = len(actual_set.intersection(predicted))
    return correct / len(actual_set)


def recall_at_k(actual_list, predicted_list, k):
    return sum(recall(actual, predicted[:k]) for actual, predicted in zip(actual_list, predicted_list)) / len(
        actual_list)

def recall_at_all(actual_list, predicted_list):
    return sum(recall(actual, predicted) for actual, predicted in zip(actual_list, predicted_list)) / len(
        actual_list)


def average_precision(actual, predicted):
    score = 0.0
    num_hits = 0
    for i, p in enumerate(predicted):
        if p in actual and p not in predicted[:i]:
            num_hits += 1
            score += num_hits / (i + 1.0)
    if not actual:
        return 0.0
    return score / len(actual)


def mean_average_precision(actual_list, predicted_list):
    return sum(average_precision(actual, predicted) for actual, predicted in zip(actual_list, predicted_list)) / len(
        actual_list)


def mean_reciprocal_rank(actual_list, predicted_list):
    rr = 0.0
    for actual, predicted in zip(actual_list, predicted_list):
        for i, p in enumerate(predicted):
            if p in actual:
                rr += 1.0 / (i + 1.0)
                break
    return rr / len(actual_list)

# # examples
# actual = [[1, 2, 3], [1, 4, 5]]
# predicted = [[1, 2, 3, 4, 5], [4, 5, 6, 7, 8]]
#
# k = 3
# precision_k = [precision_at_k(act, pred, k) for act, pred in zip(actual, predicted)]
# recall_k = [recall_at_k(act, pred, k) for act, pred in zip(actual, predicted)]
# map_score = mean_average_precision(actual, predicted)
# mrr_score = mean_reciprocal_rank(actual, predicted)
#
# print("Precision@{}: {}".format(k, precision_k))
# print("Recall@{}: {}".format(k, recall_k))
# print("MAP: {}".format(map_score))
# print("MRR: {}".format(mrr_score))