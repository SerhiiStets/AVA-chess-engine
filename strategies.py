"""
Some example strategies for people who want to create a custom, homemade bot.
And some handy classes to extend
"""

import chess
import logging
import numpy as np
from typing import Union
from chess.engine import PlayResult
from engine_wrapper import EngineWrapper

from bonuses import knight_bonuses, pawn_end_game_bonuses, pawn_middle_game_bonuses, \
    bishop_bonuses, rook_bonuses, queen_bonuses, king_middle_game_bonuses, king_end_game_bonuses

ENGAME_LIMIT = 3915

piece_mg_values: dict[int, int] = {
    chess.PAWN: 126,
    chess.ROOK: 1276,
    chess.KNIGHT: 781,
    chess.BISHOP: 825,
    chess.QUEEN: 2536,
    chess.KING: 20000
}

piece_eg_values: dict[int, int] = {
    chess.PAWN: 208,
    chess.ROOK: 1380,
    chess.KNIGHT: 854,
    chess.BISHOP: 915,
    chess.QUEEN: 2682,
    chess.KING: 20000
}

pieces_mg_bonuses: dict[int, np.ndarray[int]] = {
    chess.PAWN: pawn_middle_game_bonuses,
    chess.ROOK: rook_bonuses,
    chess.KNIGHT: knight_bonuses,
    chess.BISHOP: bishop_bonuses,
    chess.QUEEN: queen_bonuses,
    chess.KING: king_middle_game_bonuses
}


pieces_eg_bonuses: dict[int, np.ndarray[int]] = {
    chess.PAWN: pawn_end_game_bonuses,
    chess.ROOK: rook_bonuses,
    chess.KNIGHT: knight_bonuses,
    chess.BISHOP: bishop_bonuses,
    chess.QUEEN: queen_bonuses,
    chess.KING: king_end_game_bonuses
}


class FillerEngine:
    def __init__(self, main_engine, name=None):
        self.id = {
            "name": name
        }
        self.name = name
        self.main_engine = main_engine

    def __getattr__(self, method_name):
        main_engine = self.main_engine

        def method(*args, **kwargs):
            nonlocal main_engine
            nonlocal method_name
            return main_engine.notify(method_name, *args, **kwargs)

        return method


class MinimalEngine(EngineWrapper):
    def __init__(self, *args, name=None):
        super().__init__(*args)

        self.engine_name = self.__class__.__name__ if name is None else name

        self.last_move_info = []
        self.engine = FillerEngine(self, name=self.name)
        self.engine.id = {
            "name": self.engine_name
        }

    def search_with_ponder(self, board, wtime, btime, winc, binc, ponder, draw_offered):
        timeleft = 0
        if board.turn:
            timeleft = wtime
        else:
            timeleft = btime
        return self.search(board, timeleft, ponder, draw_offered)

    def search(self, board, timeleft, ponder, draw_offered):
        raise NotImplementedError("The search method is not implemented")

    def notify(self, method_name, *args, **kwargs):
        pass


class AVAChessEngine(MinimalEngine):
    """AVA chess engine."""

    def __init__(self, *args, name=None) -> None:
        super().__init__(*args, name=name)
        self._clear_logs()
        # self.openning_games = self._get_openning_games()
        self.played_openning_moves = []
        self.logger: logging.Logger = self._create_logger()

    def _clear_logs(self) -> None:
        """Cleares logs file."""
        with open("logs/debug.log", 'w') as file:
            pass

    def _get_openning_games(self) -> list[list[str]]:
        """
        Parses 8000 GM games from file and returns
        first 6 moves from these games.

        Returns:
            list[list[str]]: sorted by first move name 6 moves opennings
        """
        opennings = []
        with open("Games.txt", 'r') as file:
            for line in file.readlines():
                opennings.append([line.split()[:12]])
        return opennings.sort(key=lambda x: x[0])

    def _create_logger(self) -> logging.Logger:
        """Creates a logger for engine moves."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        file_handler = logging.FileHandler("logs/debug.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        return logger

    def _is_endgame(self, pieces_score: int) -> bool:
        """
        Checks if value of left pieces for given side is more
        then ENDGAME_LIMIT. If it is, then it's endgame.

        Args:
            pieces_score (int): combined value of left pieces

        Returns:
            bool: is this endgame for given side
        """
        return True if pieces_score <= ENGAME_LIMIT else False

    def _is_draw(self, board: chess.Board) -> bool:
        """
        Checks for possible draw scenario like stalemate, 50 move rules, etc.
        If any condition is true then the game will end in a draw.
        """
        return board.is_stalemate() or board.is_insufficient_material()\
            or board.is_seventyfive_moves() or board.is_fivefold_repetition()\
            or board.is_repetition(3)

    def _calculate_pieces_values(self, board: chess.Board, color: bool,
                                 type_of_game: dict[int, int]) -> int:
        """Calculates left pieces values.

        Args:
            board (chess.Board): chess game
            color (bool): color of given pieces
            type_of_game (dict[int, int]): endgame or middle game dict with values

        Returns:
            int: sum of calculated values
        """
        pieces_score = 0
        for piece in type_of_game:
            if piece != chess.KING:
                pieces_score += len(board.pieces(piece, color)) * type_of_game[piece]
        return pieces_score

    def _calculate_engine_depth(self, time_left: float) -> int:
        """Depending on time left for move return depth for move calculation.

        Args:
            time_left (float): time left for move in seconds

        Returns:
            int: depth for future calculation
        """
        if time_left <= 5:
            return 1
        if time_left <= 15:
            return 2
        if time_left <= 30:
            return 3
        return 4

    def _get_openning_move(self, move_number: int, white_move: bool) -> str:
        """Get openning move from parsed GM games. Not implemented yet."""
        # if move_number == 1:
        #     pass
        # if white_move:
        #     move = self.openning_games[move_number - 1 * 2]
        # else:
        #     move = self.openning_games[move_number - 1 * 2 + 1]
        raise NotImplementedError()

    def evaluate_position(self, board: chess.Board) -> float:
        """
        Evaluates game position given material, placement, etc.
        If the position is > 0 - white is winning, if < 0 - black is winning.

        Args:
            board (chess.Board): chess game board

        Returns:
            float: estimated value of the position
        """
        white_material = 0
        black_material = 0

        left_white_material = self._calculate_pieces_values(board, chess.WHITE, piece_mg_values)
        left_black_material = self._calculate_pieces_values(board, chess.BLACK, piece_mg_values)
        endgame = self._is_endgame(left_white_material) and self._is_endgame(left_black_material)

        if (endgame):
            white_material += self._calculate_pieces_values(board, chess.WHITE, piece_eg_values)
            black_material += self._calculate_pieces_values(board, chess.BLACK, piece_eg_values)
        else:
            white_material += left_white_material
            black_material += left_black_material

        # Add evaluation from bonuses depending on a square the piece is standing
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
            if piece.color == chess.WHITE:
                if endgame:
                    white_material += pieces_eg_bonuses[piece.piece_type][::-1][square]
                else:
                    white_material += pieces_mg_bonuses[piece.piece_type][::-1][square]
            else:
                if endgame:
                    black_material += pieces_eg_bonuses[piece.piece_type][square]
                else:
                    black_material += pieces_mg_bonuses[piece.piece_type][square]
        return white_material - black_material

    def _sort_moves(self, board: chess.Board) -> np.ndarray[chess.Move]:
        """
        Sort legal moves in the position with custom order.
        Following checks, captures, attack principle. 

        Args:
            board (chess.Board): chess game board

        Returns:
            np.ndarray[chess.Move]: sorted array of all legal moves
        """
        captures, checks, others = [], [], []
        for move in board.legal_moves:
            if board.is_capture(move):
                captures.append(move)
            else:
                board.push(move)
                if board.is_check:
                    checks.append(move)
                else:
                    others.append(move)
                board.pop()

        np_captures = np.array(captures)
        np_checks = np.array(checks)
        np_others = np.array(others)
        return np.concatenate((np_captures, np_checks, np_others))

    def minimax(self, board: chess.Board, depth: int, alpha: float, beta: float,
                white_move: bool) -> tuple[Union[None, chess.Move], float]:
        """Minimax Algorithm to determine the best move in the position.

        A minimax algorithm. Recursively goes through tree of legal moves evaluating the position to
        determine the best next move. Using Alpha-Beta Pruning it cuts off branches in the game tree
        which need not be searched because there already exists a better move available.

        Args:
            board (chess.Board): chess game board
            depth (int): depth of move calculation
            alpha (float): best choice found so far
            beta (float): lowest choice found so far
            white_move (bool): white or black to move

        Returns:
            tuple[Union[None, chess.Move], float]: best move and position evaluation
        """
        best_move = None

        if not depth or board.is_game_over():
            return None, self.evaluate_position(board)

        sorted_moves = self._sort_moves(board)

        if white_move:
            best_position = -float('inf')
            for move in sorted_moves:
                board.push(move)
                if board.is_checkmate():
                    current_position = float('inf')
                elif self._is_draw(board):
                    current_position = 0
                else:
                    _, current_position = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                if current_position > best_position:
                    best_move = move
                    best_position = current_position
                alpha = max(alpha, current_position)
                if beta <= alpha:
                    break
            return best_move, best_position
        else:
            best_position = float('inf')
            for move in sorted_moves:
                board.push(move)
                if board.is_checkmate():
                    current_position = -float('inf')
                elif self._is_draw(board):
                    current_position = 0
                else:
                    _, current_position = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                if current_position < best_position:
                    best_move = move
                    best_position = current_position
                beta = min(beta, current_position)
                if beta <= alpha:
                    break
            return best_move, best_position

    def search(self, board: chess.Board, timeLeft: Union[chess.engine.Limit, int], *args) -> PlayResult:
        """Starting point for chess engine required by lichess-bot.

        Args:
            board (chess.Board): chess game board
            timeLeft (Union[chess.engine.Limit, int]): time left in a position for given color

        Raises:
            error: raise error after logging it if any

        Returns:
            PlayResult: given best move from self.play method in PlayResult format
        """
        try:
            return PlayResult(self.play(board, timeLeft), None)
        except Exception as error:
            self.logger.critical(f"Error: {error}")
            raise error

    def play(self, board: chess.Board, time_left: Union[chess.engine.Limit, int]) -> chess.Move:
        """Given the timeleft and board, calculates best move in the position.

        Args:
            board (chess.Board): chess game board
            time_left (Union[chess.engine.Limit, int]): time left in a poisition for given color

        Returns:
            chess.Move: best move in a position
        """
        depth = 4

        if isinstance(time_left, int):
            # Checking if first call, which returns time control as chess.engine.Limit
            depth = self._calculate_engine_depth(time_left / 1000)

        if board.turn == chess.WHITE:
            best_move, _ = self.minimax(board, depth, -float('inf'), +float('inf'), white_move=True)
        else:
            best_move, _ = self.minimax(board, depth, -float('inf'), +float('inf'), white_move=False)

        self.logger.info(f"Depth {depth} Best move: {best_move} Move number: {board.fullmove_number}")
        self.logger.info(f"Engine evaluation: {self.evaluate_position(board) / 1000}")

        # if for some reason minimax does not proive a move
        # take random one from legal moves that are available
        if not best_move:
            for move in board.legal_moves:
                return move
        return best_move
