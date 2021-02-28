from util import *
from planning_problem import *
from search import a_star_search
from itertools import product
import os

RANDOM_PRINTS = False


class Player:
    """
    Abstract class of a player in Clue game. Each sub class is a player type
    """

    def __init__(self, character, start_location):
        self._character = character
        self._last_suggestion = None
        self._cards = set()
        self._location = start_location

    def set_location(self, loc):
        self._location = loc

    def get_location(self):
        return self._location

    def get_character(self):
        return self._character

    def add_card(self, card):
        """
        Add a card to the player's hand
        """
        self._cards.add(card)

    def get_cards(self):
        return self._cards

    def has_card(self, card):
        """
        Return true iff the player has the card in his hand
        """
        return card in self._cards

    # abstract method:
    def game_started(self):
        """
        Notifies the player that  the game has begun - mostly for initializing data structures after
        cards have been dealt
        """
        pass

    # abstract method:
    def update_on_other_player_suggestion(self, suggestion, was_showed, responders):
        """
        Get other players suggestion and information about who answerd.
        """
        pass

    # abstract method
    def see_card(self, responders, card=None):
        """
        The last responder Player shows the card to the player (following a suggestion)
        This function is also used to indicate the player that no one could
        respond to his last suggestion (if card is None)
        """
        pass

    # abstract method:
    def make_move_suggestion(self, possible_locations):
        """
        :param possible_locations: Possible location the player can go to (including current
        location)
        :return: a tuple - (move, suggestion)
        """
        pass

    # abstract method:
    def make_accusation(self):
        """
        Each turn the game asks the player for an accusation. If the player decides not to accuse,
        this function return's None
        """
        pass


class RandomPlayer(Player):
    def __init__(self, character, start_location):
        super(RandomPlayer, self).__init__(character, start_location)
        self._suspected_characters = set(CHARACTERS)
        self._suspected_weapons = set(WEAPONS)
        self._suspected_rooms = set(ROOMS)
        self._accusation = None

    def make_move_suggestion(self, possible_locations):
        relevant_room_locations = set()
        for loc in possible_locations:
            if loc in ROOMS_LOC:
                if ROOMS_LOC[loc] in self._suspected_rooms:
                    relevant_room_locations.add(loc)
        if not relevant_room_locations:
            # Then walk randomly
            self._location = random.choice(possible_locations)
            return self._location, None
        else:
            move = relevant_room_locations.pop()

            suggested_weapon = random.choice(tuple(self._suspected_weapons))

            suggested_character = random.choice(tuple(self._suspected_characters))

            suggested_room = ROOMS_LOC[move]
            if RANDOM_PRINTS:
                print("Suggested character:", suggested_character)
                print("Suggested weapon:", suggested_weapon)
                print("Suggested room:", suggested_room)
            self._last_suggestion = (suggested_character, suggested_weapon, suggested_room)
            self._location = move
            return move, (suggested_character, suggested_weapon, suggested_room)

    def see_card(self, responders, card=None):
        if not responders:
            self._accusation = self._last_suggestion
        if card in self._suspected_characters:
            self._suspected_characters.remove(card)
        if card in self._suspected_weapons:
            self._suspected_weapons.remove(card)
        if card in self._suspected_rooms:
            self._suspected_rooms.remove(card)

        # Sanity check:
        if not self._suspected_characters or not self._suspected_weapons or not self._suspected_rooms:
            print("Player", self._character, "Of type", type(self).__name__, "has empty suspects set")

    def add_card(self, card):
        self._cards.add(card)
        self.see_card(self, card)

    def make_accusation(self):
        if self._accusation:
            return self._accusation
        if len(self._suspected_characters) == 1 and len(self._suspected_weapons) == 1 and \
                len(self._suspected_rooms) == 1:
            return (self._suspected_characters.pop(), self._suspected_weapons.pop(),
                    self._suspected_rooms.pop())


class HumanPlayer(Player):
    def __init__(self, character, start_location):
        super(HumanPlayer, self).__init__(character, start_location)
        self._suspected_characters = set(CHARACTERS)
        self._suspected_weapons = set(WEAPONS)
        self._suspected_rooms = set(ROOMS)
        self.can_accuse = False

    def see_card(self, responders, card=None):
        if card:
            print("And showed us ", card)
        if not responders:
            print("not responder")
            self.can_accuse = True
        if card in self._suspected_characters:
            self._suspected_characters.remove(card)
        if card in self._suspected_weapons:
            self._suspected_weapons.remove(card)
        if card in self._suspected_rooms:
            self._suspected_rooms.remove(card)

    def make_suggestion(self, desired_location):
        """
        the human player will be able to make any suggestion
        :return:
        """
        print("Your turn, make a suggestion..")
        while True:
            print(self._suspected_characters)
            suspected_character = int(input("Type the index of the suspected character: "))
            if CHARACTERS[suspected_character - 1] not in self._suspected_characters:
                to_continue = int(input("You have chosen a character not in "
                                        "your suspects list, are you sure you "
                                        "wish to continue? 0 - Yes, 1- No"))
                if to_continue == 0:
                    break
            else:
                break

        chosen_characther = CHARACTERS[suspected_character - 1]

        while True:
            print(self._suspected_weapons)
            suspected_weapon = int(input("Type the index of the suspected weapon: "))
            if WEAPONS[suspected_weapon - 1] not in self._suspected_weapons:
                to_continue = int(input("You have chosen a weapon not in "
                                        "your suspected weapons list, are you sure you "
                                        "wish to continue? 0 - Yes, 1- No"))
                if to_continue == 0:
                    break
            else:
                break

        chosen_weapon = WEAPONS[suspected_weapon - 1]

        return (chosen_characther, chosen_weapon, desired_location)

    def make_move_suggestion(self, possible_locations):

        relevant_room_locations = set()
        locations_str = "possible locations: "
        for i in range(len(possible_locations)):
            locations_str += "( " + possible_locations[i].__str__() + " " + i.__str__() + " ) "
        print(locations_str)

        print("Your suspected rooms are: ", self._suspected_rooms)

        for loc in possible_locations:
            if loc in ROOMS_LOC:
                relevant_room_locations.add(loc)

        print("You can choose a room from the list, by typing the index beside it \n"
              "You can choose a location by typing the index beside it ")
        print("Relevant Rooms:", [ROOMS_LOC[loc] for loc in relevant_room_locations])
        while True:
            room_or_locations = input("Type 0 to choose from the possible locations; 1 - from room: ")
            if not room_or_locations.isdigit() or room_or_locations not in ['0', '1']:
                print("Only 0 and 1 are accepted!")
                continue
            chosen_location = input("Type the index (from 0) of the chosen list: ")
            if not chosen_location.isdigit() or not 0 <= int(chosen_location) < len(possible_locations):
                print("Only valid index is accepted!")
                continue
            chosen_location = int(chosen_location)
            if room_or_locations == '0':
                new_location = possible_locations[chosen_location]
                self._location = new_location
                return new_location, None
            else:
                if LOCATIONS_OF_ROOMS[ROOMS[chosen_location - 1]] in relevant_room_locations:
                    new_location = ROOMS[chosen_location - 1]
                    break
                else:
                    print("You can only choose a room you can reach!")

        self._location = new_location
        # we are in a room
        suggestion = self.make_suggestion(new_location)
        return LOCATIONS_OF_ROOMS[new_location], suggestion

    def make_accusation(self):
        # option for same as the suggestion
        # choose if you don't want to accuse
        if self.can_accuse:
            print("You can now accuse")
            print(ROOMS)
            acc_loc = int(input("Type the index of the suspected location:  "))
            acc_location = ROOMS[acc_loc - 1]
            return self.make_suggestion(acc_location)
        return None


class PlanningPlayer(Player):
    """
    Online Planning Player. Makes a plan according to a guess of who the murder
    triplate is, follows this plan until the a change occures.
    What changes can make the player replan:
    1. One of the assumed murder triplate cards is shown.
    2. Asked a question and received a different answer then expected.
    3. Aquired definite information from other player's questions.
    """

    def __init__(self, character, start_location):
        super().__init__(character, start_location)
        import time
        self.game_number = time.time()

        self._unknown_weapons = list(WEAPONS)
        self._unknown_characters = list(CHARACTERS)
        self._unknown_rooms = list(ROOMS)

        self._my_weapons = []
        self._my_characters = []
        self._my_rooms = []

        # Dictionary of cards pointing to the player who has them
        self._players_have = dict()

        # Dictionary of players pointing to combinations of cards they
        # may have - results of answers received to other player's questions.
        # Updated after every answer, we try to eliminate cards from
        # the combos to become certain
        self._players_maybe_have = dict()

        self._cards_this_player_does_not_have = dict()

        for player in CHARACTERS:
            self._players_maybe_have[player] = set()

        self._plan = []
        self._suspected_triplate = None
        self._expect_to_find_in_question = ""
        self._need_to_create_plan = True

    def make_move_suggestion(self, possible_locations):
        # We start by making a plan if we do not already have one
        if self._suspected_triplate is None:
            # Must be first round of the game
            murder_room = random.choice(self._unknown_rooms)
            murder_weapon = random.choice(self._unknown_weapons)
            murder_character = random.choice(self._unknown_characters)
            self._suspected_triplate = (
                murder_character, murder_weapon, murder_room)
            self.create_plan()

        # print(self._character, " believes in ", self._suspected_triplate)

        # Choose the first question in the plan we can ask
        for question in self._plan:
            if LOCATIONS_OF_ROOMS[question[2]] in possible_locations:
                self._location = LOCATIONS_OF_ROOMS[question[2]]
                self._last_suggestion = (question[0], question[1], question[2])
                self._expect_to_find_in_question = question[3]
                self._plan.remove(question)
                return self._location, self._last_suggestion

        # We have found no suitable question with a close room, see if any of my_rooms are close
        for room in self._my_rooms:
            if LOCATIONS_OF_ROOMS[room] in possible_locations:
                # Now lets find a question that does not expect the room as an answer
                for question in self._plan:
                    if question[3] not in ROOMS and (question[3] in CHARACTERS
                                                     or question[3] in WEAPONS):
                        # print("Had to use one of my own rooms ", room)
                        self._location = LOCATIONS_OF_ROOMS[room]
                        self._last_suggestion = (
                            question[0], question[1], room)
                        self._expect_to_find_in_question = question[3]
                        self._plan.remove(question)
                        return self._location, self._last_suggestion

        # Find the question that is closest to us and move in it's direction
        min_distance = 1000
        min_question = self._suspected_triplate
        for question in self._plan:
            distance = manhattan_distance_with_block(self._location, LOCATIONS_OF_ROOMS[question[2]])
            if distance < min_distance:
                min_distance = distance
                min_question = question

        # Find the location which will make me closest to the closest question
        min_distance = 1000
        min_location = None
        for location in possible_locations:
            distance = manhattan_distance_with_block(location, LOCATIONS_OF_ROOMS[min_question[2]])
            if distance < min_distance:
                min_distance = distance
                min_location = location
        self._location = min_location
        return min_location, None

    def update_on_other_player_suggestion(self, suggestion, was_showed, responders):
        modified_suggestion = list(suggestion)

        if self._suspected_triplate is None:
            # Must be first round of the game
            murder_room = random.choice(self._unknown_rooms)
            murder_weapon = random.choice(self._unknown_weapons)
            murder_character = random.choice(self._unknown_characters)
            self._suspected_triplate = (
                murder_character, murder_weapon, murder_room)

        if was_showed:
            player_who_answered = responders[-1]
            asked_me = self._character in responders
            need_to_fix = dict()
            # Update that the players who didn't answer do not have these cards
            not_have_responders = list(responders)
            if asked_me:
                not_have_responders.remove(self._character)
                if self._character != player_who_answered:
                    not_have_responders.remove(player_who_answered)
            else:
                not_have_responders.remove(player_who_answered)

            # Need to check if the suggestion contains one of my cards
            if suggestion[0] in self._my_characters:
                modified_suggestion.remove(suggestion[0])
                # print("I have ", suggestion[0])
            if suggestion[1] in self._my_weapons:
                modified_suggestion.remove(suggestion[1])
                # print("I have ", suggestion[1])
            if suggestion[2] in self._my_rooms:
                modified_suggestion.remove(suggestion[2])
                # print("I have ", suggestion[2])

            # Need to check if we were shown these cards, or have information about who has them
            new_modified_suggestion = list(modified_suggestion)
            for card in new_modified_suggestion:
                if card in self._players_have:
                    # We have been shown this card before
                    if self._players_have[card] != player_who_answered:
                        modified_suggestion.remove(card)
                        # print(self.get_character(), " I was already shown this card from a different player ", card)
                    else:
                        # I already know he has this, but maybe We can still deduce new information
                        if len(not_have_responders) != 0:
                            need_to_fix = self.update_players_not_have(
                                suggestion,
                                not_have_responders)
                        if len(need_to_fix) != 0:
                            self.update_deductions(need_to_fix, True)
                        return

            # Update that the players who didn't answer do not have these cards
            if len(not_have_responders) != 0:
                need_to_fix = self.update_players_not_have(suggestion,
                                                           not_have_responders)

            # Check if we know player_who_answered doesn't have one of the
            # remaining cards
            if player_who_answered in self._cards_this_player_does_not_have:
                for card in list(modified_suggestion):
                    if card in self._cards_this_player_does_not_have[player_who_answered]:
                        # print("We already know player ", player_who_answered, " does not have card ", card)
                        modified_suggestion.remove(card)

            # if len(modified_suggestion) == 0 and player_who_answered != self._character:
            #     print(
            #         "We made a mistake along the way, we got that the player who answered does not have any of the cards!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            if self._character != player_who_answered and len(modified_suggestion) == 1:
                # print("We managed to receive information from another players"
                #       " question ", modified_suggestion[0])
                need_to_fix[player_who_answered] = {modified_suggestion[0]}
            elif self._character != player_who_answered:
                self._players_maybe_have[player_who_answered].add(tuple(modified_suggestion))

            if len(need_to_fix) != 0:
                self.update_deductions(need_to_fix, True)

    def update_players_not_have(self, suggestion, not_have_responders):
        """
        Updates self._players_maybe_have that these players do not have the cards sent
        :param suggestion: cards asked
        :param not_have_responders: Players who were asked but did not answer
        :return: Dictionary holding definite information we need to update in
        the form -  {player: set of cards we found out he has}
        """
        # print("Some players did not answer the question, updating they do not have these cards")

        need_to_fix = dict()
        for character in not_have_responders:
            for card in suggestion:

                if character not in self._cards_this_player_does_not_have:
                    self._cards_this_player_does_not_have[character] = set()
                self._cards_this_player_does_not_have[character].add(card)

                new_combos = set(self._players_maybe_have[character])
                for combo in self._players_maybe_have[character]:
                    new_combo = list(combo)
                    if card in combo:
                        new_combo.remove(card)
                    if len(new_combo) == 1:
                        if character not in need_to_fix:
                            need_to_fix[character] = set()
                        need_to_fix[character].add(new_combo[0])
                    else:
                        new_combos.add(tuple(new_combo))
                self._players_maybe_have[character] = new_combos
        return need_to_fix

    def see_card(self, responders, card=None):
        need_to_rebuild_plan = False
        if responders is None:
            # print("Planning player ", self.get_character(),
            #       " has been shown no card after asking ")
            # No player had cards from our answer
            if self._last_suggestion[0] not in self._my_characters:
                self._unknown_characters.clear()
                self._unknown_characters.append(self._last_suggestion[0])
                self._suspected_triplate = (
                    self._last_suggestion[0], self._suspected_triplate[1], self._suspected_triplate[2])
            if self._last_suggestion[1] not in self._my_weapons:
                self._unknown_weapons.clear()
                self._unknown_weapons.append(self._last_suggestion[1])
                self._suspected_triplate = (
                    self._suspected_triplate[0], self._last_suggestion[1],
                    self._suspected_triplate[2])
            if self._last_suggestion[2] not in self._my_rooms:
                self._unknown_rooms.clear()
                self._unknown_rooms.append(self._last_suggestion[2])
                self._suspected_triplate = (self._suspected_triplate[0], self._suspected_triplate[1],
                                            self._last_suggestion[2])
            self.create_plan()
            # Currently not updating the dictionaries, need to figure out how, or if
            return
        responder = responders[-1]
        if card not in self._suspected_triplate:
            # print("Planning player ", self.get_character(),
            #       " is being shown ",
            #       card, " from ", responder)

            # Check if we got a different answer then expected
            if self._expect_to_find_in_question != card.name:
                # print("Planning player ", self.get_character(), "Expected card ", self._expect_to_find_in_question,
                #       " found: ", card)
                need_to_rebuild_plan = True

        # Need to update our deductions if other players did not answer
        length = len(responders)
        if length > 1:
            not_have_responders = responders[0: length - 1]
            if self._last_suggestion[2] in self._my_rooms:
                suggestion = [self._last_suggestion[0], self._last_suggestion[1]]
            else:
                suggestion = self._last_suggestion
            need_to_fix = self.update_players_not_have(suggestion,
                                                       not_have_responders)
            need_to_fix[responder] = {card}
        else:
            need_to_fix = {responder: {card}}

        self.update_deductions(need_to_fix, need_to_rebuild_plan)

    def update_deductions(self, players_and_cards, need_to_rebuild_plan):
        """
        Updated our structures players_have and players_maybe_have according
        to players_and_cards.
        :param players_and_cards: Dictionary holding definite information we
        need to updatein the form: player: set of cards we found out he has
        :param need_to_rebuild_plan: True or False
        :return: None
        """

        # print("Planning player ", self.get_character(), " is updating deductions")

        need_to_fix = players_and_cards
        while len(need_to_fix) != 0:
            new_dict = dict()
            for responder, cards in need_to_fix.items():
                for card in cards:
                    self._players_have[card] = responder

                    # We erase from the responder any combination containing this card
                    combos = list(self._players_maybe_have[responder])
                    for combo in combos:
                        if card in combo:
                            self._players_maybe_have[responder].remove(combo)

                    # Remove this card from any player who isn't responder
                    for player, maybes in self._players_maybe_have.items():
                        if player != responder:
                            new_maybes = set()
                            for combo in maybes:
                                new_combo = list(combo)
                                if card in combo:
                                    new_combo.remove(card)
                                    if len(new_combo) == 1:
                                        # Found new definite information
                                        if player not in new_dict:
                                            new_dict[player] = set()
                                        new_dict[player].add(new_combo[0])
                                        continue
                                new_maybes.add(tuple(new_combo))
                            self._players_maybe_have[player] = new_maybes

                    # Update our remaining unknowns according to the new information
                    if card in self._unknown_rooms:
                        self._unknown_rooms.remove(card)
                        need_to_rebuild_plan = True
                    if card in self._unknown_weapons:
                        self._unknown_weapons.remove(card)
                        need_to_rebuild_plan = True
                    if card in self._unknown_characters:
                        self._unknown_characters.remove(card)
                        need_to_rebuild_plan = True

                    if card in self._suspected_triplate:
                        # Creating assumed murder triplate
                        murder_room = self._suspected_triplate[2]
                        murder_weapon = self._suspected_triplate[1]
                        murder_character = self._suspected_triplate[0]
                        if card == murder_character:
                            murder_character = random.choice(self._unknown_characters)
                        elif card == murder_weapon:
                            murder_weapon = random.choice(self._unknown_weapons)
                        else:
                            murder_room = random.choice(self._unknown_rooms)

                        self._suspected_triplate = (murder_character, murder_weapon,
                                                    murder_room)
                        need_to_rebuild_plan = True
            need_to_fix = new_dict

        if need_to_rebuild_plan:
            self.create_plan()

    def add_card(self, card):
        self._cards.add(card)
        if card in WEAPONS:
            self._unknown_weapons.remove(card)
            self._my_weapons.append(card)
        if card in CHARACTERS:
            self._unknown_characters.remove(card)
            self._my_characters.append(card)
        if card in ROOMS:
            self._unknown_rooms.remove(card)
            self._my_rooms.append(card)

    def make_accusation(self):
        if len(self._unknown_rooms) == 1 and len(self._unknown_characters) == 1 and len(self._unknown_weapons) == 1:
            return self._unknown_characters[0], self._unknown_weapons[0], self._unknown_rooms[0]

    def create_plan(self):
        print("Planning player", self.get_character(), "certainly is planning something...")

        murder_room = self._suspected_triplate[2]
        murder_weapon = self._suspected_triplate[1]
        murder_character = self._suspected_triplate[0]

        # Creating the plan

        propositions = self.create_propositions()

        actions = set(self.create_actions())

        domain_file_name = str(self.game_number) + murder_character.name + "_" + murder_weapon.name \
                           + "_" + murder_room.name + "_" + self._character.name + "_domain.txt"
        domain_file = open(domain_file_name, 'w')
        domain_file.write("Propositions: \n")
        for proposition in propositions:
            domain_file.write(proposition + " ")

        domain_file.write("\nActions: \n")

        for action in actions:
            domain_file.write(action + "\n")

        domain_file.close()

        problem_file_name = str(self.game_number) + murder_character.name + "_" + \
                            murder_weapon.name + "_" + murder_room.name + "_" + self._character.name + "_problem.txt"

        problem_file = open(problem_file_name, 'w')

        problem_file.write("Initial state: ")
        for room in self._unknown_rooms:
            problem_file.write(room.name + "_unknown ")
        for character in self._unknown_characters:
            problem_file.write(character.name + "_unknown ")
        for weapon in self._unknown_weapons:
            problem_file.write(weapon.name + "_unknown ")

        problem_file.write("\nGoal state: found_character found_room found_weapon " + self._suspected_triplate[2].name)
        problem_file.close()

        # As search problem
        plan_problem = PlanningProblem(domain_file_name, problem_file_name)
        written_plan = a_star_search(plan_problem, null_heuristic, self._location)

        # print("Planning player ", self.get_character(), "plan found is: ")
        # for action in written_plan:
        #     print(action)
        # print(plan_problem.expanded)
        # print()

        # Delete the files now that we have a plan
        os.remove(domain_file_name)
        os.remove(problem_file_name)

        self._plan = []

        for action in written_plan:
            if "foundAll" not in action.name:
                action_character, action_weapon, action_room, found = \
                    action.name.split("_unknown_")

                self._plan.append((Character[action_character],
                                   Weapon[action_weapon],
                                   Room[action_room], found))

    def create_propositions(self):
        propositions = []
        for room in self._unknown_rooms:
            propositions.append(room.name + "_unknown")
            if room == self._suspected_triplate[2]:
                propositions.append(room.name + "_murder")
                propositions.append("found_room")
            else:
                propositions.append(room.name + "_player")
        for character in self._unknown_characters:
            propositions.append(character.name + "_unknown")
            if character == self._suspected_triplate[0]:
                propositions.append(character.name + "_murder")
                propositions.append("found_character")
            else:
                propositions.append(character.name + "_player")
        for weapon in self._unknown_weapons:
            propositions.append(weapon.name + "_unknown")
            if weapon == self._suspected_triplate[1]:
                propositions.append(weapon.name + "_murder")
                propositions.append("found_weapon")
            else:
                propositions.append(weapon.name + "_player")

        propositions.append(self._suspected_triplate[2].name)

        return propositions

    def create_actions(self):

        murder_character = self._suspected_triplate[0]
        murder_weapon = self._suspected_triplate[1]
        murder_room = self._suspected_triplate[2]

        action_format = "Name: {character}_{weapon}_{room}_ \n" \
                        "pre: {character} {weapon} {room} \n" \
                        "add: {to_add}\ndelete: {to_delete}"

        # First action we add is murder combo
        actions = [
            action_format.format(character=murder_character.name + "_unknown",
                                 weapon=murder_weapon.name + "_unknown",
                                 room=murder_room.name + "_unknown",
                                 to_add=murder_character.name + "_murder "
                                        + murder_weapon.name + "_murder " +
                                        murder_room.name + "_murder",
                                 to_delete="")]

        # All possible combos- We assume we cannot learn from this the murder triplate
        actions.extend(self.create_action_combinations())

        # We got all the combinations from all the other rooms, all other
        # weapons and characters should be player, now we change to found
        pre_found = "pre: "
        to_add = "\nadd: found_weapon found_character found_room " + self._suspected_triplate[2].name
        for character in self._unknown_characters:
            if character == murder_character:
                pre_found += character.name + "_murder "
            else:
                pre_found += character.name + "_player "
        for weapon in self._unknown_weapons:
            if weapon == murder_weapon:
                pre_found += weapon.name + "_murder "
            else:
                pre_found += weapon.name + "_player "
        for room in self._unknown_rooms:
            if room == murder_room:
                pre_found += room.name + "_murder "
            else:
                pre_found += room.name + "_player "

        actions.append("Name: foundAll\n" + pre_found + to_add + "\ndelete: ")
        return actions

    def create_action_combinations(self):
        """
        Helper function that creates all the action combinations.
        """
        actions = []
        characters = list(self._unknown_characters)
        weapons = list(self._unknown_weapons)
        rooms = list(self._unknown_rooms)

        # We only get one result from each question, like originally intended

        for combination in product(characters, weapons, rooms):
            character_murder = combination[0] == self._suspected_triplate[0]
            weapon_murder = combination[1] == self._suspected_triplate[1]
            room_murder = combination[2] == self._suspected_triplate[2]

            name_one = combination[0].name + "_unknown_" + combination[1].name + \
                       "_unknown_" + combination[2].name + "_unknown_" + combination[0].name
            name_two = combination[0].name + "_unknown_" + combination[1].name + \
                       "_unknown_" + combination[2].name + "_unknown_" + combination[1].name
            name_three = combination[0].name + "_unknown_" + combination[1].name + \
                         "_unknown_" + combination[2].name + "_unknown_" + combination[2].name

            pre_one = combination[0].name + "_unknown " \
                      + combination[1].name + "_unknown "
            pre_two = combination[0].name + "_unknown " \
                      + combination[1].name + "_unknown "
            pre_three = combination[0].name + "_unknown " \
                        + combination[1].name + "_unknown "

            pre_one += combination[2].name + "_unknown"
            pre_two += combination[2].name + "_unknown"
            pre_three += combination[2].name + "_unknown"

            add_one = combination[0].name + "_player"
            del_one = combination[0].name + "_unknown"

            add_two = combination[1].name + "_player"
            del_two = combination[1].name + "_unknown"

            add_three = combination[2].name + "_player"
            del_three = combination[2].name + "_unknown"

            if not character_murder:
                actions.append("Name: " + name_one + "\npre: " + pre_one +
                               "\nadd: " + add_one + "\ndelete: " + del_one)
            if not weapon_murder:
                actions.append("Name: " + name_two + "\npre: " + pre_two +
                               "\nadd: " + add_two + "\ndelete: " + del_two)
            if not room_murder:
                actions.append("Name: " + name_three + "\npre: " + pre_three +
                               "\nadd: " + add_three + "\ndelete: " + del_three)
        return actions
