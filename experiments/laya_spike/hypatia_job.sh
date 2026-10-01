#!/bin/bash
# Laya spike (step 1 of the Laya curation plan): offline checkpoint load + one choice question.
#
# From the repo root, once (checkpoint ~0.8 GB, pinned to the reviewed revision):
#   HF_HOME=data/hf uvx --from huggingface_hub hf download convaiinnovations/laya \
#       rl_agent_config.json model.safetensors tokenizer/tokenizer.json \
#       tokenizer/tokenizer_config.json encoder/config.json \
#       --revision 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
#   hpc-data data/hf
# Then:
#   hpc-submit --watch experiments/laya_spike/hypatia_job.sh

#SBATCH -p GPU
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --job-name=laya-spike
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=marco.barnfield.24@ucl.ac.uk

set -euo pipefail

# Weights come only from the pre-fetched cache; any Hub call fails loudly instead of downloading.
export HF_HOME="$PWD/../../data/hf"
export HF_HUB_OFFLINE=1
export LAYA_REVISION=reviewed

ctr nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
ctr uv run --frozen python spike.py
