"""
Some example strategies for people who want to create a custom, homemade bot.
And some handy classes to extend
"""

import chess
import logging
from typing import Union
from chess.engine import PlayResult
from engine_wrapper import EngineWrapper

from engines.bonuses import knight_bonuses, pawn_end_game_bonuses, pawn_middle_game_bonuses, \
    bishop_bonuses, rook_bonuses, queen_bonuses, king_middle_game_bonuses, king_end_game_bonuses


class FillerEngine:
    """
    Not meant to be an actual engine.

    This is only used to provide the property "self.engine"
    in "MinimalEngine" which extends "EngineWrapper"
    """

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
    """
    Subclass this to prevent a few random errors

    Even though MinimalEngine extends EngineWrapper,
    you don't have to actually wrap an engine.

    At minimum, just implement `search`,
    however you can also change other methods like
    `notify`, `first_search`, `get_time_control`, etc.
    """

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
        """
        The method to be implemented in your homemade engine

        NOTE: This method must return an instance of "chess.engine.PlayResult"
        """
        raise NotImplementedError("The search method is not implemented")

    def notify(self, method_name, *args, **kwargs):
        """
        The EngineWrapper class sometimes calls methods on "self.engine".
        "self.engine" is a filler property that notifies <self>
        whenever an attribute is called.

        Nothing happens unless the main engine does something.

        Simply put, the following code is equivalent
        self.engine.<method_name>(<*args>, <**kwargs>)
        self.notify(<method_name>, <*args>, <**kwargs>)
        """
        pass


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

pieces_mg_bonuses: dict[int, list] = {
    chess.PAWN: pawn_middle_game_bonuses,
    chess.ROOK: rook_bonuses,
    chess.KNIGHT: knight_bonuses,
    chess.BISHOP: bishop_bonuses,
    chess.QUEEN: queen_bonuses,
    chess.KING: king_middle_game_bonuses
}


pieces_eg_bonuses: dict[int, list] = {
    chess.PAWN: pawn_end_game_bonuses,
    chess.ROOK: rook_bonuses,
    chess.KNIGHT: knight_bonuses,
    chess.BISHOP: bishop_bonuses,
    chess.QUEEN: queen_bonuses,
    chess.KING: king_end_game_bonuses
}


class AVAChessEngine(MinimalEngine):
    def __init__(self, *args, name=None):
        super().__init__(*args, name=name)
        self._clear_logs()
        self.logger: logging.Logger = self._create_logger()

    def _clear_logs(self):
        with open("logs/debug.log", 'w') as file:
            pass

    def _create_logger(self) -> logging.Logger:
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
        return True if pieces_score <= ENGAME_LIMIT else False

    def _is_draw(self, board: chess.Board) -> bool:
        return board.is_stalemate() or board.is_insufficient_material()\
            or board.is_seventyfive_moves() or board.is_fivefold_repetition() or board.is_repetition(3)

    def _calculate_pieces_values(self, board: chess.Board, color: bool, type_of_game: dict[int, int]) -> int:
        pieces_score = 0
        for piece in type_of_game:
            if piece != chess.KING:
                pieces_score += len(board.pieces(piece, color)) * type_of_game[piece]
        return pieces_score

    def _calculate_engine_depth(self, time_left: float) -> int:
        if time_left <= 5:
            return 1
        elif time_left <= 15:
            return 2
        elif time_left <= 30:
            return 3
        return 4

    def evaluate_position(self, board: chess.Board) -> float:
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

    def minimax(self, board: chess.Board, depth: int, alpha: float, beta: float,
                white_move: bool) -> tuple[Union[None, chess.Move], float]:
        best_move = None

        if not depth or board.is_game_over():
            return None, self.evaluate_position(board)

        if white_move:
            best_position = -float('inf')
            for move in board.legal_moves:
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
            for move in board.legal_moves:
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
        try:
            return PlayResult(self.play(board, timeLeft), None)
        except Exception as error:
            self.logger.critical(f"Error: {error}")
            raise error

    def play(self, board: chess.Board, time_left: Union[chess.engine.Limit, int]) -> chess.Move:
        depth = 4

        if isinstance(time_left, int):
            # Checking if first call, which returns time control as chess.engine.Limit
            depth = self._calculate_engine_depth(time_left / 1000)

        if board.turn == chess.WHITE:
            best_move, _ = self.minimax(board, depth, -float('inf'), +float('inf'), white_move=True)
        else:
            best_move, _ = self.minimax(board, depth, -float('inf'), +float('inf'), white_move=False)

        self.logger.info(f"Depth {depth} Best move: {best_move}")
        self.logger.info(f"Engine evaluation: {self.evaluate_position(board) / 1000}")

        # if for some reason minimax does not proive a move
        # take random one from legal moves that are available
        if not best_move:
            for move in board.legal_moves:
                return move
        return best_move
