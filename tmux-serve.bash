#!/bin/bash
TERM=xterm-256color
tmux new -s ltrackerserve -d 'vim lost_tracker'
tmux split-window -h './env/bin/python lost_tracker/main.py'
tmux split-window 'java -jar __libs__/plovr-81ed862.jar serve plovr-config.js'
tmux select-pane -t 0
tmux resize-pane -t 1 -D 20
tmux rename-window -t ltrackerserve:0 serverout
tmux set-option remain-on-exit on
tmux bind-key r respawn-pane
tmux bind-key k kill-window
tmux attach
