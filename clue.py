from board import *
from BNplayer import *
from BNplayer2 import *
import time


class ClueGame:
    """
    A class for one single Clue game
    """

    def __init__(self, agent_types):
        self._rounds_counter = 0
        self._players = [self.__create_player(agent_types[i], CHARACTERS[i], len(agent_types))
                         for i in range(len(agent_types))]
        self._turn_index = 0
        self._board = Board(self._players)
        self._players_active = [True] * len(self._players)

        characters, weapons, rooms = list(CHARACTERS), list(WEAPONS), list(ROOMS)
        self._target_character = random.choice(characters)
        characters.remove(self._target_character)
        self._target_weapon = random.choice(weapons)
        weapons.remove(self._target_weapon)
        self._target_room = random.choice(rooms)
        rooms.remove(self._target_room)
        self._board.print_board()

        if BN in agent_types:

            cur = random.choice(characters)
            self._players[0].add_card(cur)
            characters.remove(cur)
            cur = random.choice(characters)
            self._players[0].add_card(cur)
            characters.remove(cur)

            cur = random.choice(characters)
            self._players[1].add_card(cur)
            characters.remove(cur)
            cur = random.choice(characters)
            self._players[1].add_card(cur)
            characters.remove(cur)

            cur = random.choice(characters)
            self._players[2].add_card(cur)
            characters.remove(cur)

            # Deal weapons:
            cur = random.choice(weapons)
            self._players[0].add_card(cur)
            weapons.remove(cur)

            cur = random.choice(weapons)
            self._players[1].add_card(cur)
            weapons.remove(cur)
            cur = random.choice(weapons)
            self._players[1].add_card(cur)
            weapons.remove(cur)

            cur = random.choice(weapons)
            self._players[2].add_card(cur)
            weapons.remove(cur)
            cur = random.choice(weapons)
            self._players[2].add_card(cur)
            weapons.remove(cur)

            # Deal rooms:
            cur = random.choice(rooms)
            self._players[0].add_card(cur)
            rooms.remove(cur)
            cur = random.choice(rooms)
            self._players[0].add_card(cur)
            rooms.remove(cur)
            cur = random.choice(rooms)
            self._players[0].add_card(cur)
            rooms.remove(cur)

            cur = random.choice(rooms)
            self._players[1].add_card(cur)
            rooms.remove(cur)
            cur = random.choice(rooms)
            self._players[1].add_card(cur)
            rooms.remove(cur)

            cur = random.choice(rooms)
            self._players[2].add_card(cur)
            rooms.remove(cur)
            cur = random.choice(rooms)
            self._players[2].add_card(cur)
            rooms.remove(cur)

            if characters or weapons or rooms:
                print("CARD DEALING PROBLEM")
                sys.exit()

            for player in self._players:
                player.game_started()
        else:
            deck = characters
            deck.extend(weapons)
            deck.extend(rooms)

            i = 0
            while deck:
                card_to_add = random.choice(deck)
                deck.remove(card_to_add)
                self._players[i].add_card(card_to_add)
                i = self.__advance_index_clockwise(i)

    def run(self):
        """
        Runs a single Clue game
        """
        # use this to print what we're looking for
        # self.print_cards_state()
        while True:
            winner = self.run_single_turn()
            if winner:
                print("The winner is:", winner.get_character(), "of ", str(type(winner)) + ". Game was won after",
                      self._rounds_counter, "rounds.")
                break
        # print("Main game loop ended safely")
        return winner, self._rounds_counter

    def print_board(self):
        self._board.print_board()

    def print_cards_state(self):
        """
        Prints the actual targets and each player's cards
        """
        print("MURDERER:", self._target_character)
        print("MURDER WEAPON:", self._target_weapon)
        print("MURDER ROOM:", self._target_room)

        print("*******")
        for player in self._players:
            print(player.get_character(), ':', player.get_cards())

    def run_single_turn(self):
        """
        Runs a single turn of the game
        """
        if not self._players_active[self._turn_index]:
            return
        else:
            if self._players_active.count(True) == 1:
                return self._players[self._turn_index]
        cur_player = self._players[self._turn_index]
        print(cur_player.get_character(), "'s Turn Started.")
        print("Location:", self._board.get_player_location(cur_player))
        cube_1 = np.random.randint(1, 6)
        cube_2 = np.random.randint(1, 6)
        cube_result = cube_1 + cube_2
        print("Cube:", cube_result)
        possible_locations = self._board.get_possible_locations(cur_player, cube_result)

        # Get move and suggestion from current player:
        move, suggestion = cur_player.make_move_suggestion(possible_locations)

        self._board.update_player_location(cur_player, move)
        print("Moves to:", move)
        if suggestion:
            # Run the suggestion process:
            # For now, if a player has more then one card to show, the choice is made for him randomly
            suggestion_in_order = suggestion
            suggestion = list(suggestion)
            random.shuffle(suggestion)
            cur_responder_index = self.__advance_index_clockwise(self._turn_index)
            has_responded = False
            were_asked = []
            while not has_responded and cur_responder_index != self._turn_index:
                cur_responder = self._players[cur_responder_index]
                print("Player", cur_player.get_character(), "asks", cur_responder.get_character(),
                      "if he has", suggestion)
                were_asked.append(cur_responder.get_character())
                for card in suggestion:
                    # print("Card:", card)
                    if cur_responder.has_card(card):
                        print(cur_responder.get_character(), "has responded")
                        cur_player.see_card(were_asked, card)
                        has_responded = True
                        for player in self._players:
                            if player is not cur_player:
                                player.update_on_other_player_suggestion(suggestion_in_order, True, were_asked)
                        break
                # print("###FINISH###")
                cur_responder_index = self.__advance_index_clockwise(cur_responder_index)

            # If no one could respond - inform the player:
            if not has_responded:
                cur_player.see_card(None)
                for player in self._players:
                    if player is not cur_player:
                        player.update_on_other_player_suggestion(suggestion_in_order,
                                                                 False,
                                                                 were_asked)

            # Move player that has been suggested to the suggested room
            suggested_character = suggestion_in_order[0]
            suggested_room = suggestion_in_order[2]
            for player in self._players:
                if player.get_character() == suggested_character:
                    new_loc = LOCATIONS_OF_ROOMS[suggested_room]
                    player.set_location(new_loc)
                    self._board.update_player_location(player, new_loc)
                    break

        # Run the accusation process:
        accusation = cur_player.make_accusation()
        if accusation:
            print(cur_player.get_character(), "Accused", accusation)
            accusation_character = accusation[0]
            accusation_weapon = accusation[1]
            accusation_room = accusation[2]
            if accusation_character == self._target_character \
                    and accusation_weapon == self._target_weapon \
                    and accusation_room == self._target_room:
                return cur_player
            else:
                self._players_active[self._turn_index] = False

        time.sleep(10)
        self.print_board()

        # Don't forget to pass the turn :)
        self._turn_index = self.__advance_index_clockwise(self._turn_index)
        if self._turn_index == 0:
            self._rounds_counter += 1

    def __advance_index_clockwise(self, index):
        return (index + 1) % len(self._players)

    def __create_player(self, agent_type, character, players_n):
        if agent_type == RANDOM:
            return RandomPlayer(character, OPEN_LOC[character])
        if agent_type == HUMAN:
            return HumanPlayer(character, OPEN_LOC[character])
        if agent_type == PLANNING:
            return PlanningPlayer(character, OPEN_LOC[character])
        if agent_type == BN:
            return BNPlayer(character, OPEN_LOC[character])
        if agent_type == BN2:
            return BNPlayer2(character, OPEN_LOC[character], players_n)

        print("Unknown agent type:", agent_type)
        sys.exit()


def check_input(arguments):
    usage_msg = "Usage: \n\tclue.py <player types separated by comma>\n" \
                "h - human player;\tr - random player;\tp - planning player;\tbn - the first BN player;\t" \
                "bn2 - the second BN player."

    if len(arguments) != 2:
        print(usage_msg)
        exit()
    players_args = arguments[1].split(",")
    if len(players_args) < 3:
        print(usage_msg)
        exit()
    if "bn" in players_args and (players_args.index("bn") != 0 or players_args.count("bn") != 1):
        print("The first bn can only be a member of 3-players game and has to be the first one.")
        exit()
    agent_types = []
    for player in players_args:
        if player == 'h':
            agent_types.append(HUMAN)
        elif player == 'bn':
            agent_types.append(BN)
        elif player == 'bn2':
            agent_types.append(BN2)
        elif player == 'r':
            agent_types.append(RANDOM)
        elif player == 'p':
            agent_types.append(PLANNING)
        else:
            print(usage_msg)
            exit(0)
    if len(agent_types) > 6:
        print("The number of players must be between 3 and 6 included!")
        exit()
    return agent_types


if __name__ == '__main__':
    import sys

    agent_types = check_input(sys.argv)

    if BN in agent_types:
        ROOMS.remove(Room.Library)
        ROOMS_LOC.pop(LOCATIONS_OF_ROOMS[Room.Library])
        LOCATIONS_OF_ROOMS.pop(Room.Library)

    i = 1
    while True:
        print("\n", "RUN GAME #", i)

        game = ClueGame(agent_types)
        game.run()
        if input("Wanna play again with the same characters? Press Y or y. "
                 "Otherwise, press other key: ") not in ['Y', 'y']:
            print("You quit!")
            break
        i += 1
    print("\nThanks for playing, come back again! ")
