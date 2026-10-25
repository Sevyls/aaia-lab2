# Live clip 1: reset pricing to the baseline commit and show the student regression failing.
Output video/clips/1-baseline.mp4
Source video/tapes/settings.tape

Type "echo '=== Live: reset pricing to baseline fed594c; the student regression must fail ==='" Enter
Type "git checkout fed594c -- target-service/orders/pricing.py && git status --short" Enter
Wait
Type "(cd target-service && python -m unittest discover -s tests -p test_student.py 2>&1 | tail -6)" Enter
Wait
Sleep 5s
