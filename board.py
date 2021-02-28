import numpy as np
from util import *


class Board:
    """
    A simplified board for Clue game
    """

    def __init__(self, players):
        self._locations = {player: OPEN_LOC[player.get_character()] for player in players}
        self._players = players

    def print_board(self):
        """
        Prints the board
        """
        board_to_print = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        for loc in LOCATIONS:
            if loc in ROOMS_LOC:
                board_to_print[loc[0]][loc[1]] = ROOMS.index(ROOMS_LOC[loc]) + 1
            else:
                board_to_print[loc[0]][loc[1]] = -1

        print("_" * (2 * BOARD_SIZE + 1))
        for y in range(BOARD_SIZE):
            line = "|"
            for x in range(BOARD_SIZE):
                if (y, x) in self._locations.values():
                    for player, loc in self._locations.items():
                        if loc == (y, x):
                            line += PLAYERS_SHORT[player.get_character()]
                            break
                else:
                    if board_to_print[y][x] == -1:
                        line += '_'
                    elif board_to_print[y][x] == 0:
                        line += 'X'
                    else:
                        line += board_to_print[y][x].__str__()
                line += "|"
            print(line)
        print("Where: ", end="")
        for room in Room:
            if room in ROOMS:  # not if BN is used and Library is discarded
                print(ROOMS.index(room) + 1, "-", room.name, end="; ")
        print()

    def get_possible_locations(self, player, cube_result):
        """
        Returns the possible locations that a player can move to, based on cube result
        and player's location
        """
        cur_loc = self._locations[player]
        possible_locations = []
        for loc in LOCATIONS:
            if manhattan_distance_with_block(cur_loc, loc) <= cube_result:
                possible_locations.append(loc)
        return possible_locations

    def update_player_location(self, player, new_loc):
        self._locations[player] = new_loc

    def get_player_location(self, player):
        return self._locations[player]

