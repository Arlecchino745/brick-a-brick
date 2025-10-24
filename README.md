# brick-a-brick

Using Python, implement the pathfinding problem in the "Brick-a-brick" game based on the A\* algorithm. **Since the author new to this field, please feel free to raise an issue if there are any errors or omissions.**

### Thank you
The icon is from [Iconify](https://iconify.design/).

## Overview

### About brick-a-brick

In the "brick-a-brick" game, the board is a two-dimensional matrix, and each pattern on the board appears in pairs. Players can select a pattern and slide it in any of the four directions (up, down, left, or right) **for any number of cells**. If there are no other patterns blocking the path between two identical patterns horizontally or vertically, they will be eliminated. The goal of the game is to eliminate all the patterns on the board through a reasonable sliding sequence.

### About this project

This project implements the following functions using Python:

1. Game scene generation.
    - Users can customize the board size (e.g., size=8 represents an 8×8 board).
    - Users can customize the number and distribution of pattern pairs (ensuring that each pattern appears in pairs).
    - Allows random board generation, where each position can be empty or contain a pattern (ensuring that each pattern appears in pairs).

2. Brick elimination path search. **Use the A\* algorithm to find the shortest sliding sequence to eliminate all patterns**. If the task cannot be completed, it will return "Failure."

3. Sliding cost optimization. Based on task 2, consider the sliding cost, where **different patterns have different sliding costs**. Users can customize the sliding cost for each pattern, output the final sliding sequence and total cost, and find the solution with the minimum total cost. If the task cannot be completed, return "Failure."

## License

This project is under MIT License.