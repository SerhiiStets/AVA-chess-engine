# -*- coding: utf-8 -*-
"""AVA chess engine """

import chess
from bonuses import *

# Int value of pieces to determine material for evaluation
piece_values = {
    chess.PAWN: 100,
    chess.ROOK: 500,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.QUEEN: 900,
    chess.KING: 20000
}


def evaluate_position(board):
	"""
	Evaluating position based on pieces location and material

	Parameters
	----------
	board : chess.Board
		Chess board from chess module with pieces, turns, etc.

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
			if piece.piece_type == chess.PAWN:
				white_material += pawn_bonuses[::-1][square]
			elif piece.piece_type == chess.ROOK:
				white_material += rook_bonuses[::-1][square]
			elif piece.piece_type == chess.KNIGHT:
				white_material += knight_bonuses[::-1][square]
			elif piece.piece_type == chess.BISHOP:
				white_material += bishop_bonuses[::-1][square]
			elif piece.piece_type == chess.QUEEN:
				white_material += queen_bonuses[::-1][square]
			elif piece.piece_type == chess.KING:
				if len(board.pieces(chess.QUEEN, chess.WHITE)) + len(
						board.pieces(chess.QUEEN, chess.BLACK)) == 0:
					white_material += king_end_game_bonuses[::-1][square]
				else:
					white_material += king_middle_game_bonuses[::-1][square]
			white_material += piece_values[piece.piece_type]
		else:
			if piece.piece_type == chess.PAWN:
				black_material += pawn_bonuses[square]
			elif piece.piece_type == chess.ROOK:
				black_material += rook_bonuses[square]
			elif piece.piece_type == chess.KNIGHT:
				black_material += knight_bonuses[square]
			elif piece.piece_type == chess.BISHOP:
				black_material += bishop_bonuses[square]
			elif piece.piece_type == chess.QUEEN:
				black_material += queen_bonuses[square]
			elif piece.piece_type == chess.KING:
				if len(board.pieces(chess.QUEEN, chess.WHITE)) + len(
						board.pieces(chess.QUEEN, chess.BLACK)) == 0:
					black_material += king_end_game_bonuses[square]
				else:
					black_material += king_middle_game_bonuses[square]
			black_material += piece_values[piece.piece_type]
	return white_material - black_material


def minimax(board, depth, alpha, beta, maximizing_player):
	"""
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
	list
    	Array with first element being best_move - chess.Move and second element being the
    	evaluation of the position
	"""
	best_move = ""
	if depth == 0 or board.is_game_over():
		return ["",evaluate_position(board)]
	if maximizing_player:
		value = -float('inf')
		for move in board.legal_moves:
			board.push(move)
			if board.is_checkmate():
				hypothetical_value = float('inf')
			elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves()\
					or board.is_fivefold_repetition() or board.is_repetition(3):
				hypothetical_value = 0
			else:
				hypothetical_value = minimax(board, depth - 1, alpha, beta,  False)[1]
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
				hypothetical_value = minimax(board, depth - 1, alpha, beta,  True)[1]
			board.pop()
			if hypothetical_value < value:
				best_move = move
				value = hypothetical_value
			beta = min(beta, hypothetical_value)
			if beta <= alpha:
				break
		return [best_move, value]


def play(board):
	"""
	Receives board and returns best move determined via minimax

	Parameters
	----------
	board : chess.Board
		Chess board from chess module with pieces, turns, etc.

	Returns
	-------
	chess.Move
    	The best move from minimax in the evaluated position
	"""
	if board.turn == chess.WHITE:
		best_move = minimax(board, 4, -float('inf'), +float('inf'), True)
	else:
		best_move = minimax(board, 4, -float('inf'), +float('inf'), False)
	print("\nNew Position ", evaluate_position(board) / 1000, "\n")
	return best_move[0]
