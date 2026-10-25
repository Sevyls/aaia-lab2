# Shared VHS settings; each clip tape Sources this. Run tapes from the lab root.
Set Shell "bash"
Set FontSize 20
Set Width 1920
Set Height 1080
Set Padding 24
Set TypingSpeed 15ms
Set Theme "GitHub Dark"
Set WaitTimeout 15m
Set WaitPattern /lab2\$/

Hide
Type `export VIRTUAL_ENV_DISABLE_PROMPT=1 PS1='lab2$ '; source .venv/bin/activate; clear` Enter
Sleep 1s
Show
