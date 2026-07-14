#!/usr/bin/env bash
set -euo pipefail

SESSION="devops"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux attach-session -t "$SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR" -n main
tmux send-keys -t "$SESSION":main "claude" C-m
tmux split-window -h -t "$SESSION":main -c "$PROJECT_DIR"

tmux attach-session -t "$SESSION"
