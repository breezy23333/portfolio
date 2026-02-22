# test_brain.py
from pprint import pprint
from core.brain import respond

tests = [
    "remember that my portfolio brand is Luvo Maphela",
    "recall portfolio",
    "add a todo: finish OMINEX UI",
    "list todos",
    "remove task 0",
    "convert 5 kg to lb",
    "plan to redesign my portfolio in dark mode",
    "learn https://example.com/article",
    "latest news about Bitcoin",
    "who is Ada Lovelace",
    "search DLSS vs FSR",
    "hey",
]

for t in tests:
    print("\n>", t)
    pprint(respond(t, user_name="Luvo"))