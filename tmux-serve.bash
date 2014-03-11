#!/bin/bash
TERM=xterm-256color
tmux new -s ltrackerserve -d './env/bin/python lost_tracker/main.py'
tmux split-window 'java -jar ../__libs__/plovr-eba786b34df9.jar serve plovr-config.js'
tmux rename-window -t ltrackerserve:0 serverout
tmux set-option remain-on-exit on
tmux bind-key r respawn-pane
tmux bind-key k kill-window
tmux attach
