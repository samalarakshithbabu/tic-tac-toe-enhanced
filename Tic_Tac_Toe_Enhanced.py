"""
Enhanced Tic-Tac-Toe Game with SQLite Persistence, AI, and Analytics
=====================================================================
Features:
- SQLite database for game history and move tracking
- Win rate analysis, first-move advantage, game length stats
- Minimax AI player (unbeatable)
- Random player for simulation benchmarks
- AI vs Random simulations with detailed reports
- Matplotlib charts for analytics visualization
"""

import sqlite3
import os
import random
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# =============================================================================
# DATABASE LAYER
# =============================================================================

DB_PATH = "tic_tac_toe.db"

def init_database(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Initialize database and create tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Games table - stores game results and metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner TEXT CHECK(winner IN ('X', 'O', 'Draw')),
            first_player TEXT CHECK(first_player IN ('X', 'O')),
            game_length INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            game_mode TEXT,
            x_player_type TEXT,
            o_player_type TEXT
        )
    """)
    
    # Moves table - stores every move with board state
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
            position INTEGER CHECK(position BETWEEN 0 AND 8),
            player TEXT CHECK(player IN ('X', 'O')),
            move_number INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            board_state TEXT
        )
    """)
    
    # Indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_winner ON games(winner)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON games(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_id ON moves(game_id)")
    
    conn.commit()
    return conn


def save_game(conn: sqlite3.Connection, winner: str, first_player: str, 
              game_length: int, game_mode: str, x_type: str, o_type: str) -> int:
    """Save game result to database and return game_id."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO games (winner, first_player, game_length, game_mode, x_player_type, o_player_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (winner, first_player, game_length, game_mode, x_type, o_type))
    conn.commit()
    return cursor.lastrowid


def save_move(conn: sqlite3.Connection, game_id: int, position: int, 
              player: str, move_number: int, board_state: str) -> None:
    """Record an individual move to the database."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO moves (game_id, position, player, move_number, board_state)
        VALUES (?, ?, ?, ?, ?)
    """, (game_id, position, player, move_number, board_state))
    conn.commit()


def get_all_games(conn: sqlite3.Connection) -> List[Dict]:
    """Retrieve all games from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games ORDER BY timestamp DESC")
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_game_moves(conn: sqlite3.Connection, game_id: int) -> List[Dict]:
    """Retrieve all moves for a specific game."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM moves WHERE game_id = ? ORDER BY move_number", (game_id,))
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# =============================================================================
# CORE GAME ENGINE
# =============================================================================

def _sum_three(a: int, b: int, c: int) -> int:
    """Return sum of three values."""
    return a + b + c


def print_board(xState: List[int], zState: List[int]) -> None:
    """Print the current game board."""
    zero = 'X' if xState[0] else ('O' if zState[0] else 0)
    one = 'X' if xState[1] else ('O' if zState[1] else 1)
    two = 'X' if xState[2] else ('O' if zState[2] else 2)
    three = 'X' if xState[3] else ('O' if zState[3] else 3)
    four = 'X' if xState[4] else ('O' if zState[4] else 4)
    five = 'X' if xState[5] else ('O' if zState[5] else 5)
    six = 'X' if xState[6] else ('O' if zState[6] else 6)
    seven = 'X' if xState[7] else ('O' if zState[7] else 7)
    eight = 'X' if xState[8] else ('O' if zState[8] else 8)
    
    print(f"{zero} | {one} | {two} ")
    print(f"--|---|---")
    print(f"{three} | {four} | {five} ")
    print(f"--|---|---")
    print(f"{six} | {seven} | {eight} ")


def check_win(xState: List[int], zState: List[int]) -> int:
    """
    Check for a winner.
    Returns: 1 if X wins, 0 if O wins, -1 if no winner yet.
    """
    wins = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], 
            [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for win in wins:
        if _sum_three(xState[win[0]], xState[win[1]], xState[win[2]]) == 3:
            return 1
        if _sum_three(zState[win[0]], zState[win[1]], zState[win[2]]) == 3:
            return 0
    return -1


def check_winner(xState: List[int], zState: List[int]) -> Optional[str]:
    """Return winner: 'X', 'O', or None if no winner yet."""
    wins = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], 
            [2, 5, 8], [0, 4, 8], [2, 4, 6]]
    for win in wins:
        if _sum_three(xState[win[0]], xState[win[1]], xState[win[2]]) == 3:
            return 'X'
        if _sum_three(zState[win[0]], zState[win[1]], zState[win[2]]) == 3:
            return 'O'
    return None


def is_board_full(xState: List[int], zState: List[int]) -> bool:
    """Check if board is full (draw condition)."""
    return all(xState[i] or zState[i] for i in range(9))


def is_valid_move(xState: List[int], zState: List[int], position: int) -> bool:
    """Check if a move is valid (position is empty and in range)."""
    if position < 0 or position > 8:
        return False
    return not xState[position] and not zState[position]


def get_board_string(xState: List[int], zState: List[int]) -> str:
    """Serialize board state to string for database storage."""
    return ','.join([str(xState[i]) + '|' + str(zState[i]) for i in range(9)])


def parse_board_string(board_str: str) -> Tuple[List[int], List[int]]:
    """Deserialize board state from string."""
    xState = []
    zState = []
    for pair in board_str.split(','):
        x, z = pair.split('|')
        xState.append(int(x))
        zState.append(int(z))
    return xState, zState


# =============================================================================
# AI COMPONENTS
# =============================================================================

class MinimaxPlayer:
    """Unbeatable AI using Minimax algorithm with alpha-beta pruning."""
    
    def __init__(self):
        self.player_symbol = None
        self.opponent_symbol = None
    
    def get_move(self, xState: List[int], zState: List[int], player: str) -> int:
        """Get optimal move for the given player."""
        self.player_symbol = player
        self.opponent_symbol = 'O' if player == 'X' else 'X'
        _, move = self._minimax(xState, zState, 0, True, -float('inf'), float('inf'))
        return move
    
    def _minimax(self, xState: List[int], zState: List[int], 
                 depth: int, is_maximizing: bool, alpha: float, beta: float) -> Tuple[int, int]:
        """Minimax algorithm with alpha-beta pruning."""
        # Check terminal states
        winner = check_winner(xState, zState)
        if winner == self.player_symbol:
            return 10 - depth, -1
        elif winner == self.opponent_symbol:
            return depth - 10, -1
        elif is_board_full(xState, zState):
            return 0, -1
        
        # Get available moves
        available_moves = [i for i in range(9) if is_valid_move(xState, zState, i)]
        
        if is_maximizing:
            best_score = -float('inf')
            best_move = available_moves[0]
            for move in available_moves:
                new_x = xState.copy()
                new_z = zState.copy()
                if self.player_symbol == 'X':
                    new_x[move] = 1
                else:
                    new_z[move] = 1
                score, _ = self._minimax(new_x, new_z, depth + 1, False, alpha, beta)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move
        else:
            best_score = float('inf')
            best_move = available_moves[0]
            for move in available_moves:
                new_x = xState.copy()
                new_z = zState.copy()
                if self.opponent_symbol == 'X':
                    new_x[move] = 1
                else:
                    new_z[move] = 1
                score, _ = self._minimax(new_x, new_z, depth + 1, True, alpha, beta)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score, best_move


class RandomPlayer:
    """Random AI player for simulation benchmarking."""
    
    def get_move(self, xState: List[int], zState: List[int], player: str) -> int:
        """Get a random valid move."""
        available_moves = [i for i in range(9) if is_valid_move(xState, zState, i)]
        return random.choice(available_moves) if available_moves else -1


class HumanPlayer:
    """Human player with console input."""
    
    def get_move(self, xState: List[int], zState: List[int], player: str) -> int:
        """Get move from human input."""
        while True:
            try:
                value = int(input(f"{player}'s Chance - Enter position (0-8): "))
                if 0 <= value <= 8 and is_valid_move(xState, zState, value):
                    return value
                print("Invalid position. Try again.")
            except ValueError:
                print("Please enter a number.")


# =============================================================================
# GAME EXECUTION
# =============================================================================

def play_game(x_player: Any, o_player: Any, x_type: str = "Human", 
              o_type: str = "Human", game_mode: str = "Standard",
              save_to_db: bool = True, verbose: bool = True) -> Dict:
    """
    Play a single game with specified players.
    Returns game result dictionary.
    """
    conn = init_database() if save_to_db else None
    xState = [0] * 9
    zState = [0] * 9
    turn = 'X'
    move_number = 0
    game_id = None
    
    if verbose:
        print("\n" + "=" * 50)
        print("Starting New Game")
        print("=" * 50)
    
    while True:
        if verbose:
            print_board(xState, zState)
        
        # Get move from current player
        if turn == 'X':
            move = x_player.get_move(xState, zState, 'X')
        else:
            move = o_player.get_move(xState, zState, 'O')
        
        # Apply move
        if turn == 'X':
            xState[move] = 1
        else:
            zState[move] = 1
        
        move_number += 1
        
        # Save to database
        if save_to_db and conn:
            board_str = get_board_string(xState, zState)
            if game_id is None:
                # Save game first, then moves
                pass  # Game saved after we know the winner
            save_move(conn, move, turn, move_number, board_str) if game_id else None
        
        # Check for win
        winner = check_winner(xState, zState)
        if winner is not None:
            winner_name = winner
            if verbose:
                print_board(xState, zState)
                print(f"\n{winner_name} Won the match!")
            break
        
        # Check for draw
        if is_board_full(xState, zState):
            if verbose:
                print_board(xState, zState)
                print("\nMatch over - Draw!")
            winner_name = 'Draw'
            break
        
        # Switch turn
        turn = 'O' if turn == 'X' else 'X'
    
    # Save game result
    if save_to_db and conn:
        game_id = save_game(conn, winner_name, 'X', move_number, game_mode, x_type, o_type)
        # Update moves with game_id
        cursor = conn.cursor()
        cursor.execute("UPDATE moves SET game_id = ? WHERE game_id IS NULL", (game_id,))
        conn.commit()
        conn.close()
    
    return {
        'winner': winner_name,
        'game_length': move_number,
        'x_wins': winner_name == 'X',
        'o_wins': winner_name == 'O',
        'draw': winner_name == 'Draw'
    }


def play_human_vs_human() -> None:
    """Human vs Human mode with database persistence."""
    print("\n--- Human vs Human Mode ---")
    print("Saving all games to database...")
    
    result = play_game(HumanPlayer(), HumanPlayer(), "Human", "Human", 
                       "Human vs Human", save_to_db=True, verbose=True)
    
    print(f"\nGame saved! Final score: {result['winner']} wins in {result['game_length']} moves")


def play_human_vs_ai() -> None:
    """Human vs Minimax AI mode."""
    print("\n--- Human vs AI (Minimax) Mode ---")
    print("You are playing against an unbeatable AI!")
    print("Would you like to go first? (y/n): ", end='')
    go_first = input().lower().startswith('y')
    
    if go_first:
        result = play_game(HumanPlayer(), MinimaxPlayer(), "Human", "AI", 
                           "Human vs AI", save_to_db=True, verbose=True)
    else:
        result = play_game(MinimaxPlayer(), HumanPlayer(), "AI", "Human", 
                           "Human vs AI", save_to_db=True, verbose=True)
    
    print(f"\nFinal result: {result['winner']} wins in {result['game_length']} moves")


def run_simulation(num_games: int = 1000, verbose: bool = True) -> Dict:
    """Run AI vs Random player simulation."""
    minimax = MinimaxPlayer()
    random_player = RandomPlayer()
    
    results = {
        'minimax_wins': 0,
        'random_wins': 0,
        'draws': 0,
        'games_as_first': {'minimax': 0, 'random': 0},
        'games_as_second': {'minimax': 0, 'random': 0}
    }
    
    if verbose:
        print(f"\n--- Running {num_games} Games: Minimax vs Random ---")
        start_time = time.time()
    
    for i in range(num_games):
        # Alternate who goes first
        minimax_goes_first = i % 2 == 0
        
        if minimax_goes_first:
            result = play_game(minimax, random_player, "Minimax", "Random",
                              "Simulation", save_to_db=True, verbose=False)
            results['games_as_first']['minimax'] += 1
            results['games_as_second']['random'] += 1
            # X is Minimax when going first
            if result['x_wins']:
                results['minimax_wins'] += 1
            elif result['o_wins']:
                results['random_wins'] += 1
            else:
                results['draws'] += 1
        else:
            result = play_game(random_player, minimax, "Random", "Minimax",
                              "Simulation", save_to_db=True, verbose=False)
            results['games_as_first']['random'] += 1
            results['games_as_second']['minimax'] += 1
            # O is Minimax when going second
            if result['o_wins']:
                results['minimax_wins'] += 1
            elif result['x_wins']:
                results['random_wins'] += 1
            else:
                results['draws'] += 1
        
        if verbose and (i + 1) % (num_games // 10) == 0:
            print(f"  Progress: {i + 1}/{num_games} games completed...")
    
    if verbose:
        elapsed = time.time() - start_time
        print(f"\nCompleted {num_games} games in {elapsed:.2f} seconds")
    
    return results


# =============================================================================
# ANALYTICS
# =============================================================================

def calculate_win_rates(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Calculate overall win rates by player."""
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("SELECT COUNT(*) FROM games")
    total_games = cursor.fetchone()[0]
    
    if total_games == 0:
        return {'total_games': 0}
    
    cursor.execute("SELECT winner, COUNT(*) FROM games GROUP BY winner")
    results = cursor.fetchall()
    
    win_counts = {'X': 0, 'O': 0, 'Draw': 0}
    for winner, count in results:
        win_counts[winner] = count
    
    return {
        'total_games': total_games,
        'x_wins': win_counts['X'],
        'o_wins': win_counts['O'],
        'draws': win_counts['Draw'],
        'x_win_rate': win_counts['X'] / total_games * 100,
        'o_win_rate': win_counts['O'] / total_games * 100,
        'draw_rate': win_counts['Draw'] / total_games * 100
    }


def analyze_first_move_advantage(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Analyze first-move advantage statistics."""
    cursor = conn.cursor()
    
    # First player wins when going first as X
    cursor.execute("""
        SELECT winner, COUNT(*) 
        FROM games 
        WHERE first_player = 'X' 
        GROUP BY winner
    """)
    x_first_results = dict(cursor.fetchall())
    
    # First player wins when going first as O
    cursor.execute("""
        SELECT winner, COUNT(*) 
        FROM games 
        WHERE first_player = 'O' 
        GROUP BY winner
    """)
    o_first_results = dict(cursor.fetchall())
    
    first_player_wins = x_first_results.get('X', 0) + o_first_results.get('O', 0)
    second_player_wins = x_first_results.get('O', 0) + o_first_results.get('X', 0)
    draws = x_first_results.get('Draw', 0) + o_first_results.get('Draw', 0)
    
    total = first_player_wins + second_player_wins + draws
    first_move_win_rate = first_player_wins / total * 100 if total > 0 else 0
    
    return {
        'first_player_wins': first_player_wins,
        'second_player_wins': second_player_wins,
        'draws': draws,
        'first_move_win_rate': first_move_win_rate,
        'first_player_as_X': x_first_results,
        'first_player_as_O': o_first_results
    }


def get_game_length_distribution(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Analyze game length distribution."""
    cursor = conn.cursor()
    cursor.execute("SELECT game_length, winner FROM games")
    games = cursor.fetchall()
    
    length_counts = defaultdict(lambda: {'X': 0, 'O': 0, 'Draw': 0})
    total_lengths = []
    
    for length, winner in games:
        length_counts[length][winner] += 1
        total_lengths.append(length)
    
    avg_length = sum(total_lengths) / len(total_lengths) if total_lengths else 0
    
    return {
        'distribution': dict(length_counts),
        'average_length': avg_length,
        'min_length': min(total_lengths) if total_lengths else 0,
        'max_length': max(total_lengths) if total_lengths else 0
    }


def analyze_opening_moves(conn: sqlite3.Connection) -> Dict[int, Dict[str, int]]:
    """Analyze opening move effectiveness."""
    cursor = conn.cursor()
    
    # Get first move of each game
    cursor.execute("""
        SELECT m.position, g.winner, g.first_player
        FROM moves m
        JOIN games g ON m.game_id = g.id
        WHERE m.move_number = 1
    """)
    opening_moves = cursor.fetchall()
    
    opening_stats = {}
    for pos in range(9):
        opening_stats[pos] = {'X': 0, 'O': 0, 'Draw': 0, 'total': 0}
    
    for position, winner, first_player in opening_moves:
        opening_stats[position][winner] += 1
        opening_stats[position]['total'] += 1
    
    return opening_stats


def get_ai_simulation_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get AI vs Random simulation statistics."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT x_player_type, o_player_type, COUNT(*) as games,
               SUM(CASE WHEN winner = 'X' THEN 1 ELSE 0 END) as x_wins,
               SUM(CASE WHEN winner = 'O' THEN 1 ELSE 0 END) as o_wins,
               SUM(CASE WHEN winner = 'Draw' THEN 1 ELSE 0 END) as draws
        FROM games
        WHERE game_mode = 'Simulation'
        GROUP BY x_player_type, o_player_type
    """)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'x_type': row[0],
            'o_type': row[1],
            'games': row[2],
            'x_wins': row[3],
            'o_wins': row[4],
            'draws': row[5]
        })
    
    return results


# =============================================================================
# REPORTING
# =============================================================================

def print_summary_report(conn: sqlite3.Connection) -> None:
    """Print comprehensive analytics report."""
    print("\n" + "=" * 60)
    print("TIC-TAC-TOE ANALYTICS REPORT")
    print("=" * 60)
    
    win_rates = calculate_win_rates(conn)
    print(f"\n📊 OVERALL STATISTICS")
    print(f"   Total Games: {win_rates['total_games']}")
    print(f"   X Wins: {win_rates['x_wins']} ({win_rates['x_win_rate']:.1f}%)")
    print(f"   O Wins: {win_rates['o_wins']} ({win_rates['o_win_rate']:.1f}%)")
    print(f"   Draws: {win_rates['draws']} ({win_rates['draw_rate']:.1f}%)")
    
    first_move = analyze_first_move_advantage(conn)
    print(f"\n🎯 FIRST-MOVE ANALYSIS")
    print(f"   First Player Wins: {first_move['first_player_wins']}")
    print(f"   Second Player Wins: {first_move['second_player_wins']}")
    print(f"   Draws: {first_move['draws']}")
    print(f"   First-Move Win Rate: {first_move['first_move_win_rate']:.1f}%")
    
    game_lengths = get_game_length_distribution(conn)
    print(f"\n⏱️ GAME LENGTH STATISTICS")
    print(f"   Average Length: {game_lengths['average_length']:.1f} moves")
    print(f"   Shortest Game: {game_lengths['min_length']} moves")
    print(f"   Longest Game: {game_lengths['max_length']} moves")
    
    print(f"\n📈 OPENING MOVE ANALYSIS")
    openings = analyze_opening_moves(conn)
    for pos, stats in sorted(openings.items(), key=lambda x: -x[1]['total'])[:5]:
        win_pct = (stats['X'] + stats['O']) / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"   Position {pos}: {stats['total']} games, Win Rate: {win_pct:.1f}%")
    
    print("\n" + "=" * 60)


def generate_charts(conn: sqlite3.Connection, output_dir: str = ".") -> List[str]:
    """Generate matplotlib charts for analytics."""
    charts = []
    
    # 1. Win Rate Comparison
    win_rates = calculate_win_rates(conn)
    if win_rates.get('total_games', 0) > 0:
        fig, ax = plt.subplots(figsize=(8, 5))
        categories = ['X Wins', 'O Wins', 'Draws']
        values = [win_rates['x_wins'], win_rates['o_wins'], win_rates['draws']]
        colors = ['#3498db', '#e74c3c', '#95a5a6']
        bars = ax.bar(categories, values, color=colors)
        ax.set_ylabel('Number of Games')
        ax.set_title('Win Rate Distribution')
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                   str(val), ha='center', va='bottom')
        plt.tight_layout()
        path = os.path.join(output_dir, 'win_rate_comparison.png')
        plt.savefig(path)
        plt.close()
        charts.append(path)
    
    # 2. First Move Advantage
    first_move = analyze_first_move_advantage(conn)
    total = first_move['first_player_wins'] + first_move['second_player_wins'] + first_move['draws']
    if total > 0:
        fig, ax = plt.subplots(figsize=(7, 7))
        sizes = [first_move['first_player_wins'], 
                 first_move['second_player_wins'], 
                 first_move['draws']]
        labels = ['First Player Wins', 'Second Player Wins', 'Draws']
        colors = ['#2ecc71', '#9b59b6', '#95a5a6']
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('First-Move Advantage Analysis')
        path = os.path.join(output_dir, 'first_move_advantage.png')
        plt.savefig(path)
        plt.close()
        charts.append(path)
    
    # 3. Game Length Distribution
    game_lengths = get_game_length_distribution(conn)
    if game_lengths.get('distribution'):
        lengths = list(game_lengths['distribution'].keys())
        x_wins = [game_lengths['distribution'][l].get('X', 0) for l in lengths]
        o_wins = [game_lengths['distribution'][l].get('O', 0) for l in lengths]
        draws = [game_lengths['distribution'][l].get('Draw', 0) for l in lengths]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        x_pos = range(len(lengths))
        width = 0.25
        ax.bar([p - width for p in x_pos], x_wins, width, label='X Wins', color='#3498db')
        ax.bar(x_pos, o_wins, width, label='O Wins', color='#e74c3c')
        ax.bar([p + width for p in x_pos], draws, width, label='Draws', color='#95a5a6')
        ax.set_xlabel('Game Length (moves)')
        ax.set_ylabel('Number of Games')
        ax.set_title('Game Length Distribution by Outcome')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(lengths)
        ax.legend()
        plt.tight_layout()
        path = os.path.join(output_dir, 'game_length_distribution.png')
        plt.savefig(path)
        plt.close()
        charts.append(path)
    
    # 4. Opening Move Heatmap
    openings = analyze_opening_moves(conn)
    board_data = []
    for row in range(3):
        row_data = []
        for col in range(3):
            pos = row * 3 + col
            stats = openings.get(pos, {'total': 0, 'X': 0, 'O': 0, 'Draw': 0})
            win_pct = (stats['X'] + stats['O']) / stats['total'] * 100 if stats['total'] > 0 else 0
            row_data.append(win_pct)
        board_data.append(row_data)
    
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(board_data, cmap='YlGn', interpolation='nearest')
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels([0, 1, 2])
    ax.set_yticklabels([0, 1, 2])
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    ax.set_title('Opening Move Win Rate (%)')
    
    # Add text annotations
    for i in range(3):
        for j in range(3):
            text = ax.text(j, i, f'{board_data[i][j]:.0f}%',
                          ha="center", va="center", color="black", fontsize=14)
    
    plt.colorbar(im)
    path = os.path.join(output_dir, 'opening_move_heatmap.png')
    plt.savefig(path)
    plt.close()
    charts.append(path)
    
    return charts


def print_simulation_report(results: Dict) -> None:
    """Print simulation results report."""
    total = (results['minimax_wins'] + results['random_wins'] + 
             results['draws'])
    
    print("\n" + "=" * 60)
    print("SIMULATION RESULTS: MINIMAX vs RANDOM")
    print("=" * 60)
    print(f"\n📊 SUMMARY")
    print(f"   Total Games: {total}")
    print(f"   Minimax Wins: {results['minimax_wins']} ({results['minimax_wins']/total*100:.1f}%)")
    print(f"   Random Wins: {results['random_wins']} ({results['random_wins']/total*100:.1f}%)")
    print(f"   Draws: {results['draws']} ({results['draws']/total*100:.1f}%)")
    
    print(f"\n🎯 STRATEGIC INSIGHTS")
    minimax_as_first = results['games_as_first']['minimax']
    minimax_as_second = results['games_as_second']['minimax']
    print(f"   Minimax going first: {minimax_as_first} games")
    print(f"   Minimax going second: {minimax_as_second} games")
    
    if results['minimax_wins'] > results['random_wins'] * 5:
        print(f"\n✅ Minimax demonstrates overwhelming advantage over random play.")
        print(f"   The optimal strategy beats random choices >95% of the time.")
    elif results['random_wins'] > 0:
        print(f"\n⚠️ Random player won some games against Minimax.")
        print(f"   This indicates imperfect Minimax play or edge cases.")
    else:
        print(f"\n🏆 Perfect results - Minimax never loses to random!")
    
    print("=" * 60)


# =============================================================================
# ORIGINAL CLASSIC MODE (Backward Compatible)
# =============================================================================

def play_classic() -> None:
    """Original game - backward compatible."""
    print("\n--- Classic Mode (Original Game) ---")
    xState = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    zState = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    turn = 1  # 1 for X and 0 for O
    print("Welcome to Tic Tac Toe")
    
    while True:
        print_board(xState, zState)
        if turn == 1:
            print("X's Chance")
            value = int(input("Please enter a value: "))
            xState[value] = 1
        else:
            print("O's Chance")
            value = int(input("Please enter a value: "))
            zState[value] = 1
        cwin = check_win(xState, zState)
        if cwin != -1:
            print("Match over")
            break
        turn = 1 - turn


# =============================================================================
# MAIN MENU
# =============================================================================

def main():
    """Main menu with all options."""
    while True:
        print("\n" + "=" * 50)
        print("  🎮 ENHANCED TIC-TAC-TOE")
        print("=" * 50)
        print("1. Human vs Human (with DB tracking)")
        print("2. Human vs AI (Minimax)")
        print("3. Quick Simulation (100 games)")
        print("4. Full Simulation (1000 games)")
        print("5. Analytics Dashboard")
        print("6. Generate Charts")
        print("7. Classic Game (Original)")
        print("8. Exit")
        print("=" * 50)
        
        choice = input("Enter your choice (1-8): ").strip()
        
        if choice == '1':
            play_human_vs_human()
        elif choice == '2':
            play_human_vs_ai()
        elif choice == '3':
            results = run_simulation(100)
            print_simulation_report(results)
        elif choice == '4':
            results = run_simulation(1000)
            print_simulation_report(results)
        elif choice == '5':
            conn = init_database()
            print_summary_report(conn)
            conn.close()
        elif choice == '6':
            conn = init_database()
            charts = generate_charts(conn)
            print(f"\n✅ Generated {len(charts)} charts:")
            for c in charts:
                print(f"   - {c}")
            conn.close()
        elif choice == '7':
            play_classic()
        elif choice == '8':
            print("Thanks for playing!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()