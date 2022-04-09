# -*- coding: utf-8 -*-
"""
AVA chess engine

AVA is a simple chess engine for lichess.org. You can play against it on lichess

Todos:
- if low on time, lower depth
- save best lines and if they proceed do not load minimax again
- bonuses for double rooks, pawns, etc

@Author: Serhii Stets
"""

import sys
import chess
import chess.engine
import logging

from typing import Union

from engines.bonuses import knight_bonuses, pawn_end_game_bonuses, pawn_middle_game_bonuses, \
    bishop_bonuses, rook_bonuses, queen_bonuses, king_middle_game_bonuses, king_end_game_bonuses


# Int value of pieces to determine material for evaluation
piece_values = {
    chess.PAWN: 100,
    chess.ROOK: 500,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.QUEEN: 900,
    chess.KING: 20000
}


def is_endgame(board: chess.Board) -> bool:
    """Checks if the game is in endgame to later use different bonuses for pawns and kings.

    Parameters
    ----------
    board : chess.Board
        Chess board from chess module with pieces, turns, etc

    Returns
    -------
    bool
        if the game is in endgame return True, if not return False
    """
    white_queen = len(board.pieces(chess.QUEEN, chess.WHITE))
    black_queen = len(board.pieces(chess.QUEEN, chess.BLACK))
    white_rooks = len(board.pieces(chess.ROOK, chess.WHITE))
    black_rooks = len(board.pieces(chess.ROOK, chess.BLACK))
    white_knights = len(board.pieces(chess.KNIGHT, chess.WHITE))
    black_knights = len(board.pieces(chess.KNIGHT, chess.BLACK))
    white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
    black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
    if not white_queen + black_queen and white_rooks + white_bishops + white_knights <= 3 and black_rooks + black_bishops + black_knights <= 3:
        return True
    elif white_rooks + white_bishops + white_knights <= 1 and black_rooks + black_bishops + black_knights <= 1 and white_queen + black_queen <= 2:
        return True
    return False


def evaluate_position(board: chess.Board) -> float:
    """Evaluating position based on pieces location and material

    Parameters
    ----------
    board : chess.Board
        Chess board from chess module with pieces, turns, etc

    Returns
    -------
    float
        The evaluation of the position (if + white wining, if - black wining)
    """
    white_material = black_material = 0
    # Add evaluation from bonuses depending on a square the piece is standing
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue
        if piece.color == chess.WHITE:
            white_material += rook_bonuses[::-1][square] if piece.piece_type == chess.ROOK else 0
            white_material += knight_bonuses[::-1][
                square] if piece.piece_type == chess.KNIGHT else 0
            white_material += bishop_bonuses[::-1][
                square] if piece.piece_type == chess.BISHOP else 0
            white_material += queen_bonuses[::-1][square] if piece.piece_type == chess.QUEEN else 0
            if is_endgame(board):
                white_material += pawn_end_game_bonuses[::-1][square] if piece.piece_type == chess.PAWN else 0
                white_material += king_end_game_bonuses[::-1][square] if piece.piece_type == chess.KING else 0
                white_material += (50 * 1 / len(board.pieces(piece.piece_type, chess.WHITE))) + \
                                  piece_values[piece.piece_type]
            else:
                white_material += pawn_middle_game_bonuses[::-1][square] if piece.piece_type == chess.PAWN else 0
                white_material += king_middle_game_bonuses[::-1][square] if piece.piece_type == chess.KING else 0
                white_material += piece_values[piece.piece_type]
        else:
            black_material += rook_bonuses[square] if piece.piece_type == chess.ROOK else 0
            black_material += knight_bonuses[square] if piece.piece_type == chess.KNIGHT else 0
            black_material += bishop_bonuses[square] if piece.piece_type == chess.BISHOP else 0
            black_material += queen_bonuses[square] if piece.piece_type == chess.QUEEN else 0
            if is_endgame(board):
                black_material += pawn_end_game_bonuses[square] if piece.piece_type == chess.PAWN else 0
                black_material += king_end_game_bonuses[square] if piece.piece_type == chess.KING else 0
                black_material += (50 * 1 / len(board.pieces(piece.piece_type, chess.BLACK))) + \
                                  piece_values[piece.piece_type]
            else:
                black_material += pawn_middle_game_bonuses[square] if piece.piece_type == chess.PAWN else 0
                black_material += king_middle_game_bonuses[square] if piece.piece_type == chess.KING else 0
                black_material += piece_values[piece.piece_type]
    return white_material - black_material


def minimax(board: chess.Board, depth: int, alpha: float, beta: float, maximizing_player: bool) -> list[chess.Move, float]:
    """Minimax Algorithm to determine the best move in the position.

    A minimax algorithm. Recursively goes through tree of legal moves evaluating the position to
    determine the best next move. Using Alpha-Beta Pruning it cuts off branches in the game tree
    which need not be searched because there already exists a better move available.

    Parameters
    ----------
    board : chess.Board
        Chess board from chess module with pieces, turns, etc.
    depth : int
        Depth of tree search
    alpha : float
        Best value that the maximizer (white) can guarantee
    beta : float
        Best value that the minimizer (black) can guarantee
    maximizing_player : bool
        Which turn is it (True - white, False - black)

    Returns
    -------
    list[chess.Move, float]
        Array with first element being best_move - chess.Move and second element being the
        evaluation of the position
    """
    best_move = ""
    if not depth or board.is_game_over():
        return ["", evaluate_position(board)]
    if maximizing_player:
        value = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                hypothetical_value = float('inf')
            elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() \
                    or board.is_fivefold_repetition() or board.is_repetition(3):
                hypothetical_value = 0
            else:
                hypothetical_value = minimax(board, depth - 1, alpha, beta, False)[1]
            board.pop()
            if hypothetical_value > value:
                best_move = move
                value = hypothetical_value
            alpha = max(alpha, hypothetical_value)
            if beta <= alpha:
                break
        return [best_move, value]
    else:
        value = float('inf')
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                hypothetical_value = -float('inf')
            else:
                hypothetical_value = minimax(board, depth - 1, alpha, beta, True)[1]
            board.pop()
            if hypothetical_value < value:
                best_move = move
                value = hypothetical_value
            beta = min(beta, hypothetical_value)
            if beta <= alpha:
                break
        return [best_move, value]


def play(board: chess.Board, time_left: Union[chess.engine.Limit, int]) -> chess.Move:
    """Receives board and returns best move determined via minimax.

    Parameters
    ----------
    board : chess.Board
        Chess board from chess module with pieces, turns, etc
    time_left : Union[chess.engine.Limit, int]
        If first call, return chess.engine.Limit which is what time control is chosen
        On second and other calls returns time left on a clock for the next move

    Returns
    -------
    chess.Move
        The best move from minimax in the evaluated position
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s - %(levelname)s - %(message)s")

    if isinstance(time_left, int):      # Checking if first call, which returns time control as chess.engine.Limit
        if time_left / 1000 <= 15:
            depth = 1                   # if time left is lower than 15 seconds then we are going to make a one mover
        elif time_left / 1000 <= 30:
            depth = 2                   # if time left is lower than 30 seconds, decrees depth to 2
        elif time_left / 1000 <= 60 * 3:
            depth = 3                   # if time left is lower than 3 minutes, decrees depth to 3
        else:
            depth = 4                   # in any other case use depth = 4
    else:
        depth = 4

    try:
        if board.turn == chess.WHITE:
            best_move = minimax(board, depth, -float('inf'), +float('inf'), True)
        else:
            best_move = minimax(board, depth, -float('inf'), +float('inf'), False)
        logging.info(f"Best move: {best_move[0]}")
        logging.info(f"New Position: {evaluate_position(board) / 1000}")
        logging.info(f"Depth: {depth}")
        if best_move[0] == "":
            return board.legal_moves[0]
        return best_move[0]
    except Exception as error:
        logging.critical(f"Error: {error}")
