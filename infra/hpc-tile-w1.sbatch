#!/bin/bash
#SBATCH --job-name=dc-tile-w1
#SBATCH --partition=scavenge
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=%x-%j.log
#SBATCH --account=pi_sk2433
#SBATCH --qos=normal

# Determinism + throughput probe: generate production region r.-16.-1
# (blocks x -8192..-7681, z -512..-1) on the HPC stack, timed.
# Success = RESULT JSON with status PASS; the region ships back for a
# byte-level comparison against production before any bulk work.
set -euo pipefail
cd ~/diffusion_model_infinite_test

# CUDA userspace if the TD CUDA backend needs it (harmless if absent).
module load CUDA/12.6.0 2>/dev/null || true
export JAVA_HOME="$HOME/diffusion_model_infinite_test/bundle/jdk"
export PATH="$JAVA_HOME/bin:$PATH"

# TD variant under test is selected by which jar sits in app/mods.
# The setup step places exactly one terrain-diffusion jar there.
/usr/bin/python3.11 hpc/hpc_chunky_tile.py \
  --app "$HOME/diffusion_model_infinite_test/bundle/app" \
  --work "$HOME/diffusion_model_infinite_test/work-tile-w1" \
  --java "$HOME/diffusion_model_infinite_test/bundle/jdk" \
  --models "$HOME/diffusion_model_infinite_test/bundle/models/terrain-diffusion-models" \
  --seed -6008857613538391475 \
  --level-type 'drewcraft\:terrain_diffusion_scale_3' \
  --center -7936 -256 \
  --radius 800 \
  --rcon-port 25580 \
  --server-port 25565
