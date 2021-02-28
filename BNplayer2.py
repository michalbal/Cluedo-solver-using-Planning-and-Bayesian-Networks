from player import *
from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination, Inference
import itertools


class BNPlayer2(Player):

    def __init__(self, character, start_location, players_n):
        super().__init__(character, start_location)
        self.model = None
        self.my_index = CHARACTERS.index(character)  # I'm player number -
        #  dictionaries name: cpd
        self.weapons_cpds = dict()
        self.room_cpds = dict()
        self.character_cpds = dict()
        # accusation material
        self.murder_char = None
        self.murder_weapon = None
        self.murder_room = None

        self.murder_card_ind = players_n  # is the number of players
        self.card_vals_range = self.murder_card_ind + 1  # The last is Murder-card

    def update_on_other_player_suggestion(self, suggestion, was_showed, responders):
        if not self.model:
            self.create_model()
        parents = [suggestion[0].name, suggestion[1].name, suggestion[2].name]
        # For players that didn't answer update that they answered False (0) on the triplet
        players_didnt_answer = responders[:-1]
        for p in players_didnt_answer:
            name, cpd = self.three_cards_q(parents[0], parents[1], parents[2], CHARACTERS.index(p))
            self.update_p_of_parents_given_child(parents, name, 0)
            self.model.remove_node(name)
        if was_showed:
            # For player that showed card update that one of them may be his
            player_answered = responders[-1]
            name, cpd = self.three_cards_q(parents[0], parents[1], parents[2], CHARACTERS.index(player_answered))
            self.update_p_of_parents_given_child(parents, name, 1)
            self.model.remove_node(name)

    def see_card(self, responders, card=None):
        # If card wasn't shown - it's the result
        if not card:
            self.murder_char, self.murder_weapon, self.murder_room = self._last_suggestion
            return

        parents = [self._last_suggestion[0].name, self._last_suggestion[1].name, self._last_suggestion[2].name]
        # For players that didn't answer update that they answered False (0) on the triplet
        players_didnt_answer = responders[:-1]
        for p in players_didnt_answer:
            name, cpd = self.three_cards_q(parents[0], parents[1], parents[2], CHARACTERS.index(p))
            self.update_p_of_parents_given_child(parents, name, 0)
            self.model.remove_node(name)
        # For player that showed card update player-exactly-this-card
        player_answered = responders[-1]
        name = card.name + "P" + str(CHARACTERS.index(player_answered))
        self.update_p_of_parents_given_child([card], name, 1)

    def make_move_suggestion(self, possible_locations):
        if not self.model:
            self.create_model()
        # weapon is assumed murder weapon, otherwise - high % one
        weapon = self.murder_weapon if self.murder_weapon else Weapon[
            self.most_probable_murder_card(self.weapons_cpds)[0]]
        # character is assumed culprit, otherwise - high % one
        character = self.murder_char if self.murder_char else Character[
            self.most_probable_murder_card(self.character_cpds)[0]]
        # weapon is assumed murder weapon, otherwise - None if all are unreachable and room.name if reachable
        if self.murder_room:
            room = self.murder_room
            if LOCATIONS_OF_ROOMS[room] in possible_locations:
                self._last_suggestion = (character, weapon, room)
                return LOCATIONS_OF_ROOMS[room], self._last_suggestion
        probable_rooms = self.most_probable_murder_card(self.room_cpds)
        room = None
        for p_room in probable_rooms:
            if LOCATIONS_OF_ROOMS[Room[p_room]] in possible_locations:
                room = Room[p_room]
                break
        if room is None:
            # all probable rooms are unreachable, move towards highest P room
            self._last_suggestion = None
            return find_location_closest_to_m_room(possible_locations, probable_rooms[0]), None
        self._last_suggestion = (character, weapon, room)
        return LOCATIONS_OF_ROOMS[room], self._last_suggestion

    def most_probable_murder_card(self, cpds):
        """
        Goes through all cards, checks the probability of it being the secret murder card. Sorts from higher to lower
        probability.
        :param cpds: Conditional Probability Distribution tables (and their names) to get probability from.
        :return: sorted list of probable murder cards (excludes impossibles (P = 0)).
        """
        card_prob_dict = dict()
        for name in cpds:
            card_prob_dict[name] = cpds[name].values[self.murder_card_ind]
        card_prob_dict = {k: v for k, v in sorted(card_prob_dict.items(), key=lambda item: item[1], reverse=True)}
        # use this to print current probabilities distribution
        # print(card_prob_dict)
        ordered_l = [v for v in card_prob_dict if card_prob_dict[v] != 0]  # what was returned before

        if card_prob_dict[ordered_l[0]] >= 0.97 or len(ordered_l) == 1:  # probability for accusation
            if ordered_l[0] in Room.__members__:
                self.murder_room = Room[ordered_l[0]]
            elif ordered_l[0] in Character.__members__:
                self.murder_char = Character[ordered_l[0]]
            else:
                self.murder_weapon = Weapon[ordered_l[0]]
        return ordered_l

    def make_accusation(self):
        if self.murder_char and self.murder_weapon and self.murder_room:
            return self.murder_char, self.murder_weapon, self.murder_room
        return None

    def create_model(self):
        """
        Create Dynamic Bayesian Model of the game (updated and changed during the gamerun)
        """
        self.model = BayesianModel()
        # Create weapons
        self.model_group(util.WEAPONS, self.weapons_cpds)
        # Create rooms
        self.model_group(util.ROOMS, self.room_cpds)
        # Create chars
        self.model_group(util.CHARACTERS, self.character_cpds)
        # Answer one card one player
        self.exact_card_ans_by_player()

    def exact_card_ans_by_player(self):
        """
        Tables for answers to our question. This update is for a situation where it's known exactly which card was
        revealed by which player.
        """
        for j in range(self.murder_card_ind):  # murder-card can't answer questions
            for group in [self.character_cpds, self.weapons_cpds, self.room_cpds]:
                for card in group:
                    name = card + "P" + str(j)
                    self.model.add_edge(card, name)
                    has_card_true = []
                    for value in range(self.card_vals_range):
                        has_card_true.append(1 if value == j else 0)
                    has_card_false = [1 - v for v in has_card_true]
                    tbl = [has_card_false, has_card_true]
                    cpd = TabularCPD(name, 2, tbl, evidence=[card],
                                     evidence_card=[self.card_vals_range])
                    self.model.add_cpds(cpd)

    def three_cards_q(self, character, weapon, room, player_ind):
        """
        Adds CPDs to our model for a triplet of Char-Weapon-Room that is either answered or not by given player.
        Probability is True if at least one belongs to the player and False otherwise.
        :param character: Character card name
        :param weapon: Weapon card name
        :param room: Room card name
        :param player_ind: index of current player
        :return: name of the created node and added CPD
        """
        name = character + "_" + weapon + "_" + room + "P" + str(player_ind)
        self.model.add_edge(character, name)
        self.model.add_edge(weapon, name)
        self.model.add_edge(room, name)
        balanced_true = []
        for comb in itertools.product(range(self.card_vals_range), repeat=3):
            if any(comb[i] == player_ind for i in range(len(comb))):
                balanced_true.append(1)
            else:
                balanced_true.append(0)
        balanced_false = [1 - v for v in balanced_true]
        tbl = [balanced_false, balanced_true]
        cpd = TabularCPD(name, 2, tbl, evidence=[character, weapon, room],
                         evidence_card=[self.card_vals_range] * 3)
        self.model.add_cpds(cpd)
        return name, cpd

    def model_group(self, cards, cpd_dic):
        """
        Creates models for a given group of cards. Variable is the name of the card, values are player indexes and one
        more out of range, that is murder-card.
        :param cards: Cards of the given group (e.x. weapons cards)
        :param cpd_dic: dictionary to save the resulting tables
        """
        for card in cards:
            if card in self._cards:
                tbl = [[1] if i == self.my_index else [0] for i in range(self.card_vals_range)]
            else:
                tbl = [[1 / (self.card_vals_range - 1)] if i != self.my_index else [0] for i in
                       range(self.card_vals_range)]
            w = TabularCPD(card.name, self.card_vals_range, tbl)
            cpd_dic[card.name] = w
            self.model.add_node(card.name)
            self.model.add_cpds(w)

    def update_p_of_parents_given_child(self, parents, card_type, value):
        """
        Update probabilities of parents considering that card_type has given value
        :param parents:
        :param card_type:
        :param value:
        :return:
        """
        #  balance variables
        var_elim = VariableElimination(self.model)
        for v in parents:
            if type(v) != str:
                v = v.name
            new_vals = var_elim.query(variables=[v], evidence={card_type: value},
                                      show_progress=False)
            original_vals = self.model.get_cpds(v)
            original_vals.values = new_vals.values


def find_location_closest_to_m_room(possible_locations, goal_room):
    """
    Finds reachable location closest to given room
    :param possible_locations: list of reachable coordinates
    :param goal_room: room name
    :return: location closest to the goal
    """
    location = possible_locations[0]
    distance = float('inf')
    for p_location in possible_locations:
        this_dist = util.manhattan_distance_with_block(p_location, LOCATIONS_OF_ROOMS[Room[goal_room]])
        if this_dist < distance:
            distance = this_dist
            location = p_location
    return location
