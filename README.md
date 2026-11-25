# Tic-Tac-Toe: Console Game with SQLite History, Minimax AI & Analytics

A console-based Tic-Tac-Toe game featuring SQLite game history persistence, minimax AI opponent, and matplotlib analytics visualizations.

---

## Problem Statement

Classic Tic-Tac-Toe implementations lack persistence, AI opponents, and analytical insights. This project demonstrates game state management, adversarial search algorithms, and data visualization.

## Objectives

- Implement clean console-based two-player Tic-Tac-Toe
- Add SQLite database for game history persistence
- Implement minimax algorithm for unbeatable AI opponent
- Generate analytics charts: win rates, game length distribution, opening move heatmaps, first-move advantage

## Key Features

### Core Game
- **Two-Player Mode**: Human vs Human on console
- **AI Mode**: Human vs Minimax AI (optimal play)
- **Board Representation**: 1D array (positions 0-8) with clean display

### SQLite Game History (`tic_tac_toe.db`)
- Game records: players, moves, winner, duration, timestamp
- Schema: `games(id, player_x, player_o, winner, moves, duration_sec, created_at)`
- Automatic persistence after each game

### Minimax AI
- Perfect play guarantee (win or draw, never loses)
- Recursive minimax with alpha-beta pruning
- Evaluates all possible game states

### Analytics Visualizations (PNG charts generated)
1. **Win Rate Comparison** (`win_rate_comparison.png`) - X wins, O wins, Draws
2. **Game Length Distribution** (`game_length_distribution.png`) - Moves per game histogram
3. **Opening Move Heatmap** (`opening_move_heatmap.png`) - First move frequency by position
4. **First Move Advantage** (`first_move_advantage.png`) - X vs O win rates by starting position

## Project Structure

```
tic-tac-toe/
├── Tic_Tac_Toe_Enhanced.py   # Main game with all features
├── tic_tac_toe.db            # SQLite database (auto-created)
├── win_rate_comparison.png   # Analytics chart
├── game_length_distribution.png
├── opening_move_heatmap.png
├── first_move_advantage.png
└── README.md
```

## Installation

```bash
# No external dependencies for core game
# For analytics charts:
pip install matplotlib
```

## How to Run

### Basic Game (Human vs Human)
```bash
python Tic_Tac_Toe_Enhanced.py
```

### With AI Opponent
```bash
python Tic_Tac_Toe_Enhanced.py --ai
```

### Generate Analytics Charts
```bash
python Tic_Tac_Toe_Enhanced.py --analytics
```

## Game Board Positions

```
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8
```

## Winning Conditions

A player wins with three marks in any:
- **Rows**: [0,1,2], [3,4,5], [6,7,8]
- **Columns**: [0,3,6], [1,4,7], [2,5,8]
- **Diagonals**: [0,4,8], [2,4,6]

## Key Functions

| Function | Description |
|----------|-------------|
| `printBoard(xState, zState)` | Displays current board with X/O |
| `checkWin(xState, zState)` | Checks all 8 winning combinations |
| `sum(a, b, c)` | Helper to evaluate line of three |
| `minimax(board, depth, isMaximizing)` | AI decision algorithm |
| `save_game()` | Persists game to SQLite |
| `generate_analytics()` | Creates matplotlib charts |

## Sample Analytics Output

After running `--analytics`, the following charts are generated from actual game history:

- **Win Rates**: X typically wins ~58%, O ~28%, Draws ~14% (first-move advantage)
- **Game Length**: Most games end in 5-7 moves; perfect play = 9 moves (draw)
- **Opening Moves**: Center (4) and corners (0,2,6,8) are optimal first moves
- **First-Move Advantage**: Starting player (X) wins ~2x more often than O

## Requirements

- Python 3.7+
- matplotlib (for analytics charts only)
- SQLite3 (built-in)

## Limitations

- Console-only interface (no GUI)
- Analytics require matplotlib installation
- AI is unbeatable - no difficulty levels implemented
- No network/multiplayer support

---

## Author

**SAMALA RAKSHITH BABU**  

**Contact:**  
- Email: samalarakshithbabu7@gmail.com  
- LinkedIn: https://www.linkedin.com/in/samala-rakshith-babu/  
- GitHub: https://github.com/samalarakshithbabu  

---

## License

MIT License