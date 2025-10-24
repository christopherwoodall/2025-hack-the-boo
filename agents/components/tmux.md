- You must use `tmux` for any shell interactions.
- Connect to the tmux session named `agent-tmux`.
- Attach to the first window (index 0) and the second pane (index 1).
- Only run commands in the attached tmux pane.
- Use the following command to attach to the session:

```bash
tmux attach-session -t agent-tmux:0.1
```