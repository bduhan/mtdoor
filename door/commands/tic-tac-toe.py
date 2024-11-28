# This file adds a command to the mtdoor node-bot.
# the 'ttt' command will play tic-tac-toe
# with the user using only Meshtastic text messages

from . import BaseCommand
from loguru import logger as log
import random
import re


class TicTacToe(BaseCommand):
    command = "ttt"
    description = "Tic-Tac-Toe - Human vs Computer"
    help = "'ttt' to play tic-tac-toe"

    def load(self):
        self.board = {}
        self.turn = {}

    def invoke(self, msg: str, node: str) -> str:

        response = ""

        # See if the user wants to exit
        if msg.lower().split()[0] == "exit":
            self.persistent_session(node, False)
            del self.board[node]
            return "Goodbye"

        # Set up a persistent session
        self.persistent_session(node, True)

        # Set up new game if none in progress
        if not self.board.get(node, False):
            # Initialize the board as a list of empty spaces
            self.board[node] = [" " for _ in range(9)]
            self.turn[node] = "X"
            response += "Welcome to Tic-Tac-Toe! You are X, the computer is O.\n\n"

        # Player move
        input = extract_number(msg.lower())
        if input:
            try:
                move = input - 1
                if self.board[node][move] != " ":
                    response += "This spot is already taken. Try again.\n"
                else:
                    self.board[node][move] = "X"
                    self.turn[node] = "O"
            except (ValueError, IndexError):
                response += "Invalid input. Try again.\n"
                self.turn[node] = "X"

        # Check if the player won
        if check_winner(self.board[node], "X"):
            response += "Congratulations! You win!\n"
            self.turn[node] = "end"

        # Check if the board is full
        if is_board_full(self.board[node]):
            response += "It's a tie!\n"
            self.turn[node] = "end"

        # Computer Move
        if self.turn[node] == "O":
            self.board[node][computer_move(self.board[node])] = "O"
            self.turn[node] = "X"

            # Check if the computer won
            if check_winner(self.board[node], "O"):
                response += "The computer wins. Better luck next time!\n"
                self.turn[node] = "end"

            # Check if the board is full
            if is_board_full(self.board[node]):
                response += "It's a tie!\n"
                self.turn[node] = "end"

        response += display_board(self.board[node])

        if self.turn[node] == "end":
            response += "Good game! Send 'ttt' to play again.\n"
            self.persistent_session(node, False)
            del self.board[node]
        else:
            response += "Please enter a number between 1 and 9 or 'exit' to quit.\n"

        return response


# Function to display the board
def display_board(board):
    symbol = {}
    symbol["X"] = " X "
    symbol["O"] = " O "
    symbol[" "] = " _ "
    output = f"{symbol[board[0]]}{symbol[board[1]]}{symbol[board[2]]}\n"
    output += f"{symbol[board[3]]}{symbol[board[4]]}{symbol[board[5]]}\n"
    output += f"{symbol[board[6]]}{symbol[board[7]]}{symbol[board[8]]}\n"
    return output


# Check if there is a winner
def check_winner(board, player):
    win_combinations = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],  # Rows
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],  # Columns
        [0, 4, 8],
        [2, 4, 6],  # Diagonals
    ]
    for combination in win_combinations:
        if all(board[pos] == player for pos in combination):
            return True
    return False


# Check if the board is full
def is_board_full(board):
    return " " not in board


# Function to make the computer's move
def computer_move(board):
    # Check if the computer can win in the next move
    for i in range(9):
        if board[i] == " ":
            board[i] = "O"
            if check_winner(board, "O"):
                return i
            board[i] = " "

    # Check if the player can win in the next move, and block them
    for i in range(9):
        if board[i] == " ":
            board[i] = "X"
            if check_winner(board, "X"):
                return i
            board[i] = " "

    # Take the center if available
    if board[4] == " ":
        return 4

    # Take a random corner if available
    corners = [i for i in [0, 2, 6, 8] if board[i] == " "]
    if corners:
        return random.choice(corners)

    # Take any remaining space
    for i in range(9):
        if board[i] == " ":
            return i


def extract_number(input_string):
    # Use regex to match optional 'ttt', followed by optional whitespace, and then a number
    match = re.search(r"^(?:ttt\s*)?(\d+)", input_string.strip())
    if match:
        return int(match.group(1))
    else:
        return None
