# Live clip 2: qwen3:8b repairs pricing through native tool calls.
# The only scripted input is "yes" at the approval prompt, disclosed on screen.
Output video/clips/2-live.mp4
Source video/tapes/settings.tape

Type "echo '=== Live run: qwen3:8b with native tool calls (yes at the approval prompt is typed by the recording script) ==='" Enter
Type `python starter/agent.py --root target-service --model qwen3:8b --task "$(cat task.txt)"; echo "exit code: $?"` Enter
Wait /Type yes:/
Sleep 6s
Type "yes" Enter
Wait
Sleep 6s
