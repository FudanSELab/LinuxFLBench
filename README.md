# LinuxFLBench

This repository contains the code and data for the paper "LinuxFLBench: Benchmarking and Enhancing LLM-based Agents in Localizing Linux Kernel Bugs".

## Dataset Introduction

LINUXFLBENCH is a new benchmark of 250 Fault Localization tasks derived from real-world Linux kernel bugs.

- The dataset is located at `dataset/LINUXFLBENCH_dataset.jsonl` in JSON Lines format.
- Each line is a real Linux kernel bug sample, with fields including:
  - `id`: Bug ID
  - `title`: Bug title
  - `description`: Detailed bug description
  - `patch`: Patch content for the fix
  - `paths`: Source file paths involved (i.e., localization target files)
  - `methods`: Function names involved
  - Additional metadata: kernel version, component, hardware, etc.
- The dataset covers various kernel subsystems and is suitable for evaluating LLM/agent-based localization and repair.

## Methods and Code Structure

The main code is under the `code/` directory, organized as follows:

- `scale/`: Candidate file expansion and reasoning
  - `scaling_candidates_with_dir.py`: Directory-based candidate expansion
  - `scaling_candidates_with_guess.py`: LLM-based candidate expansion
- `merge/`: Multi-model/multi-method result fusion and reranking
  - `merge.py`: Fusion of multiple ranking results
  - `rerank.py`: LLM-based candidate reranking
- `eval/`: Evaluation and metrics
  - `evaluate.py`: Main evaluation script
  - `evaluation_metrics.py`: Common metrics such as Recall@K, MRR
- `utils.py`, `file_parser.py`: General utility functions

### Typical Workflow

1. **Candidate Expansion**  
   Use scripts in `scale/` to expand candidate file lists for each bug (e.g., Directory-Aware Expansion, Potential Cause Expansion).
2. **Candidate Integration**  
   Use scripts in `merge/` to fuse multiple candidate ranking results, and rerank with LLM.
3. **Evaluation**  
   Use scripts in `eval/` to evaluate the final results with metrics such as Recall@K and MRR.

## Requirements

This project requires Python 3.8+ and the following packages:

- openai
- jsonlines

Install dependencies with pip:

```bash
pip install openai jsonlines
```

Some scripts require configuration of OpenAI API Key and base_url. See script arguments for details.

## Quick Start

Example: Directory-Aware Expansion

```bash
python code/scale/scaling_candidates_with_dir.py \
  --data_path dataset/LINUXFLBENCH_dataset.jsonl \
  --save_path results/dir_scaling.jsonl \
  --gpt_base_url https://api.openai.com/v1 \
  --api_key YOUR_API_KEY \
  --kernel_path /path/to/linux/kernel/
```

Evaluate the results:

```bash
python code/eval/evaluate.py --path results/dir_scaling.jsonl
```

For more details, usage, or questions, please open an issue or contact the authors.
