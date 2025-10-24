import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "src",
    ],
    "includes": [
        "src",
        "src._types",
        "src.a_star",
        "src.action_log",
        "src.board_gen",
        "src.eliminate",
        "src.successor",
    ],
    "excludes": [
        "test",
        "tests",
        "pytest",
        "unittest",
        "tkinter",
    ],
    "include_files": [
        ("data/board_example.json", "data/board_example.json"),
    ],
    "optimize": 1,
}

base = None
if sys.platform == "win32":
    base = None


executables = [
    Executable(
        "main.py",
        base=base,
        target_name="brick-a-brick.exe",
        icon="static/icon.ico",
        copyright="Copyright (C) 2025 Arlecchino745",
    )
]


setup(
    name="brick-a-brick",
    version="1.0.0",
    description="implement the pathfinding problem in the \"Brick-a-brick\" game based on the A* algorithm.",
    author="Arlecchino745",
    options={"build_exe": build_exe_options},
    executables=executables,
)
