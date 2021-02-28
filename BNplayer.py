from player import *
from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
import numpy as np
from util import *
import itertools
import pandas as pd
from player import *
from scipy.stats import entropy


class BNPlayer(Player):
    def __init__(self, character, start_location):
        super(BNPlayer, self).__init__(character, start_location)
        self._suspected_characters = set(CHARACTERS)
        self._suspected_weapons = set(WEAPONS)
        self._suspected_rooms = set(ROOMS)
        self._accusation = None
        self._accusation_entropy_threshold = 0
        self._suspects_model = None
        self._weapons_model = None
        self._rooms_model = None
        self._suspects_in_order = None
        self._weapons_in_order = None
        self._rooms_in_order = None
        self._suspects_evidence_table = None
        self._character_to_player_index = {Character.MrGreen: 2, Character.ProfPlum: 3}

        # Create queues of variables to insert to:
        self._p2_suspects_queue = Queue()
        self._p2_weapons_queue = Queue()
        self._p2_rooms_queue = Queue()
        self._p3_suspects_queue = Queue()
        self._p3_weapons_queue = Queue()
        self._p3_rooms_queue = Queue()

        self._p3_suspects_queue.push('s1_p3')
        self._p2_suspects_queue.push('s2_p2')
        self._p2_suspects_queue.push('s1_p2')

        self._p3_weapons_queue.push('w2_p3')
        self._p3_weapons_queue.push('w1_p3')
        self._p2_weapons_queue.push('w2_p2')
        self._p2_weapons_queue.push('w1_p2')

        self._p3_rooms_queue.push('r2_p3')
        self._p3_rooms_queue.push('r1_p3')
        self._p2_rooms_queue.push('r2_p2')
        self._p2_rooms_queue.push('r1_p2')

    def add_card(self, card):
        self._cards.add(card)
        if card in self._suspected_characters:
            self._suspected_characters.remove(card)
        if card in self._suspected_weapons:
            self._suspected_weapons.remove(card)
        if card in self._suspected_rooms:
            self._suspected_rooms.remove(card)

    def game_started(self):
        self._suspects_model, self._weapons_model, self._rooms_model = create_models(len(self._suspected_characters),
                                                                                     len(self._suspected_weapons),
                                                                                     len(self._suspected_rooms))

        self._suspects_in_order = list(self._suspected_characters)
        self._weapons_in_order = list(self._suspected_weapons)
        self._rooms_in_order = list(self._suspected_rooms)

        # Because there are 3 variables of other players' card in the BN
        self._suspects_evidence_table = normalized(np.ones((len(self._suspects_in_order), 3)))

    def update_on_other_player_suggestion(self, suggestion, was_showed, responders):
        """
        Suggestion is character, weapon, room. respondres are the characters.
        Was showed is bool
        """
        node = ""
        if was_showed:
            for i in range(len(responders) - 1):
                if self._character is responders[i]:
                    continue
                self.player_doesnt_have_card(self._character_to_player_index[responders[i]], suggestion[0])
                self.player_doesnt_have_card(self._character_to_player_index[responders[i]], suggestion[1])
                self.player_doesnt_have_card(self._character_to_player_index[responders[i]], suggestion[2])

    def see_card(self, responders, card=None):
        if not responders:
            self._accusation = self._last_suggestion
            return

        suggestion = self._last_suggestion

        for i in range(len(responders) - 1):
            if self._character is responders[i]:
                continue
            self.player_doesnt_have_card(self._character_to_player_index[responders[i]], suggestion[0])
            self.player_doesnt_have_card(self._character_to_player_index[responders[i]], suggestion[1])
            self.player_doesnt_have_card(self._character_to_player_index[responders[i]], suggestion[2])

        self.player_has_card(self._character_to_player_index[responders[-1]], card)

    def make_move_suggestion(self, possible_locations):
        loc = self.closest_most_probable_location(possible_locations)
        self._location = loc
        if loc not in ROOMS_LOC:
            return loc, None
        most_probable_suspect = self.get_most_probable_suspect()
        most_probable_weapon = self.get_most_probable_weapon()
        most_probable_room = self.get_closest_most_probable_room()
        self._last_suggestion = (most_probable_suspect, most_probable_weapon, most_probable_room)
        return loc, (most_probable_suspect, most_probable_weapon, most_probable_room)

    def make_accusation(self):
        if self._accusation:
            return self._accusation

        s_infer = VariableElimination(self._suspects_model)
        s_dis = s_infer.query(variables=['s'], show_progress=False)
        w_infer = VariableElimination(self._weapons_model)
        w_dis = w_infer.query(variables=['w'], show_progress=False)
        r_infer = VariableElimination(self._rooms_model)
        r_dis = r_infer.query(variables=['r'], show_progress=False)

        if entropy(s_dis.values) <= self._accusation_entropy_threshold and \
                entropy(w_dis.values) <= self._accusation_entropy_threshold and \
                entropy(r_dis.values) <= self._accusation_entropy_threshold:
            return self._suspects_in_order[list(s_dis.values).index(max(list(s_dis.values)))], \
                   self._weapons_in_order[list(w_dis.values).index(max(list(w_dis.values)))], \
                   self._rooms_in_order[list(r_dis.values).index(max(list(r_dis.values)))]

    def print_beliefs(self):

        s_infer = VariableElimination(self._suspects_model)
        s_dis = s_infer.query(variables=['s'], show_progress=False)
        print(s_dis)
        print(self._suspects_in_order)

        w_infer = VariableElimination(self._weapons_model)
        w_dis = w_infer.query(variables=['w'], show_progress=False)
        print(w_dis)
        print(self._weapons_in_order)

        r_infer = VariableElimination(self._rooms_model)
        r_dis = r_infer.query(variables=['r'], show_progress=False)
        print(r_dis)
        print(self._rooms_in_order)

    def player_has_card(self, player_index, card):
        """
        Update bayesian models so that a player has a card. The card must be a suspected card (not in hand)
        :param player_index: Either 2 or 3.
        :param card: the card
        """
        if type(card) is Character:
            i = self._suspects_in_order.index(card)
            if player_index == 2:
                node = self._p2_suspects_queue.pop()
            if player_index == 3:
                node = self._p3_suspects_queue.pop()
            if not node:
                return
            # Make query about source:
            s_infer = VariableElimination(self._suspects_model)
            s_dis = s_infer.query(variables=['s'], evidence={node: i}, show_progress=False)
            s_cpd = self._suspects_model.get_cpds('s')
            s_cpd.values = s_dis.values

            # Update node's cpd s.t node's value is known:
            nodes_cpd = self._suspects_model.get_cpds(node)
            nodes_cpd.values = np.zeros(nodes_cpd.values.shape)
            nodes_cpd.values[i] = 1

        if type(card) is Weapon:
            i = self._weapons_in_order.index(card)
            if player_index == 2:
                node = self._p2_weapons_queue.pop()
            if player_index == 3:
                node = self._p3_weapons_queue.pop()

            if not node:
                return

            # Make query about source:
            w_infer = VariableElimination(self._weapons_model)
            w_dis = w_infer.query(variables=['w'], evidence={node: i}, show_progress=False)
            w_cpd = self._weapons_model.get_cpds('w')
            w_cpd.values = w_dis.values
            # Update node's cpd s.t node's value is known:
            nodes_cpd = self._weapons_model.get_cpds(node)
            nodes_cpd.values = np.zeros(nodes_cpd.values.shape)
            nodes_cpd.values[i] = 1

        if type(card) is Room:
            i = self._rooms_in_order.index(card)
            if player_index == 2:
                node = self._p2_rooms_queue.pop()
            if player_index == 3:
                node = self._p3_rooms_queue.pop()

            if not node:
                return

            # Make query about source:
            r_infer = VariableElimination(self._rooms_model)
            r_dis = r_infer.query(variables=['r'], evidence={node: i}, show_progress=False)
            r_cpd = self._rooms_model.get_cpds('r')
            r_cpd.values = r_dis.values
            # Update node's cpd s.t node's value is known:
            nodes_cpd = self._rooms_model.get_cpds(node)
            nodes_cpd.values = np.zeros(nodes_cpd.values.shape)
            nodes_cpd.values[i] = 1

    def player_doesnt_have_card(self, player_index, card):
        """
        Update cpd's so that a player doesnt have a card. The card must be a suspected card (not in hand)
        :param player_index: Either 2 or 3.
        :param card: the card
        """
        # Just initialize the variables
        i = 0
        most_probable_index = 0
        nodes = []
        cpds = []

        if type(card) is Character:
            if card not in self._suspected_characters:
                return
            i = self._suspects_in_order.index(card)
            most_probable_index = self._suspects_in_order.index(self.get_most_probable_suspect())
            if player_index == 2:
                nodes.append("s1_p2")
                nodes.append("s2_p2")
            if player_index == 3:
                nodes.append("s1_p3")
            for node in nodes:
                cpds.extend([self._suspects_model.get_cpds(node)])

        if type(card) is Weapon:
            if card not in self._suspected_weapons:
                return
            i = self._weapons_in_order.index(card)
            most_probable_index = self._weapons_in_order.index(self.get_most_probable_weapon())
            if player_index == 2:
                nodes.append("w1_p2")
                nodes.append("w2_p2")
            if player_index == 3:
                nodes.append("w1_p3")
                nodes.append("w2_p3")
            for node in nodes:
                cpds.extend([self._weapons_model.get_cpds(node)])

        if type(card) is Room:
            if card not in self._suspected_rooms:
                return
            i = self._rooms_in_order.index(card)
            most_probable_index = self._rooms_in_order.index(self.get_closest_most_probable_room())
            if player_index == 2:
                nodes.append("r1_p2")
                nodes.append("r2_p2")
            if player_index == 3:
                nodes.append("r1_p3")
                nodes.append("r2_p3")
            for node in nodes:
                cpds.extend([self._rooms_model.get_cpds(node)])

        for cpd in cpds:
            cpd.values[i] = 0
            normalize_cpd(cpd, most_probable_index)

    def closest_most_probable_location(self, possible_locations):
        """
        The code explain itself better then I could ever do.
        """
        most_probable_room = self.get_closest_most_probable_room()
        return min(possible_locations,
                   key=lambda y: manhattan_distance_with_block(LOCATIONS_OF_ROOMS[most_probable_room], y))

    def get_most_probable_suspect(self):
        """
        The code explain itself better then I could ever do.
        """
        s_infer = VariableElimination(self._suspects_model)
        s_dis = s_infer.query(variables=['s'], show_progress=False).values
        return self._suspects_in_order[list(s_dis).index(max(s_dis))]

    def get_most_probable_weapon(self):
        """
        The code explain itself better then I could ever do.
        """
        w_infer = VariableElimination(self._weapons_model)
        w_dis = w_infer.query(variables=['w'], show_progress=False).values
        return self._weapons_in_order[list(w_dis).index(max(w_dis))]

    def get_closest_most_probable_room(self):
        """
        Return the most probable room. If there are many, return the closest of course
        """
        r_infer = VariableElimination(self._rooms_model)
        r_dis = list(r_infer.query(variables=['r'], show_progress=False).values)
        m = max(r_dis)
        most_probable_rooms = []
        for i in range(len(r_dis)):
            if r_dis[i] == m:
                most_probable_rooms.append(self._rooms_in_order[i])
        return min(most_probable_rooms, key=lambda x: manhattan_distance_with_block(self._location,
                                                                                    LOCATIONS_OF_ROOMS[x]))


def normalized(a):
    """
    :param a: a numpy array
    :return: normalized array column wise
    """
    return a/a.sum(0)


def all_different(*args):
    s = set()
    for x in args:
        s.add(x)
    return len(s) == len(args)


def create_cpd_table(rank, domain_size):
    """
    :param rank: rank is the number of nodes getting IN the node variable associated with this table
    :param domain_size: The size of the domain of the node variable associated with this table
    :return: The initial cpd table with uniform distribution
    """
    a = normalized(np.ones((domain_size, 1)))
    if rank == 0:
        return a

    if rank == 1:
        for i in (range(domain_size)):
            new = np.ones((domain_size, 1))
            new[i] = 0
            a = np.concatenate((a, normalized(new)), axis=1)
        a = np.delete(a, 0, axis=1)
        return a

    if rank == 2:
        for i, j in itertools.product(range(domain_size), range(domain_size)):
            if i == j:
                a = np.concatenate((a, normalized(np.ones((domain_size, 1)))), axis=1)
                continue
            new = np.ones((domain_size, 1))
            new[i] = 0
            new[j] = 0
            a = np.concatenate((a, normalized(new)), axis=1)
        a = np.delete(a, 0, axis=1)
        return a

    if rank == 3:
        for i, j, k in itertools.product(range(domain_size), range(domain_size), range(domain_size)):
            # If not all different:
            if not all_different(i, j, k):
                a = np.concatenate((a, normalized(np.ones((domain_size, 1)))), axis=1)
                continue
            new = np.ones((domain_size, 1))
            new[i] = 0
            new[j] = 0
            new[k] = 0
            a = np.concatenate((a, normalized(new)), axis=1)
        a = np.delete(a, 0, axis=1)
        return a

    if rank == 4:
        for i, j, k, l in itertools.product(range(domain_size), range(domain_size),
                                            range(domain_size), range(domain_size)):
            # If not all different:
            if not all_different(i, j, k, l):
                a = np.concatenate((a, normalized(np.ones((domain_size, 1)))), axis=1)
                continue
            new = np.ones((domain_size, 1))
            new[i] = 0
            new[j] = 0
            new[k] = 0
            new[l] = 0
            a = np.concatenate((a, normalized(new)), axis=1)
        a = np.delete(a, 0, axis=1)
        return a

    if rank == 5:
        for i, j, k, l, m in itertools.product(range(domain_size), range(domain_size),
                                            range(domain_size), range(domain_size), range(domain_size)):
            # If not all different:
            if not all_different(i, j, k, l, m):
                a = np.concatenate((a, normalized(np.ones((domain_size, 1)))), axis=1)
                continue
            new = np.ones((domain_size, 1))
            new[i] = 0
            new[j] = 0
            new[k] = 0
            new[l] = 0
            new[m] = 0
            a = np.concatenate((a, normalized(new)), axis=1)
        a = np.delete(a, 0, axis=1)
        return a


def create_models(hidden_suspects, hidden_weapons, hidden_rooms):
    """
    Creates Bayesian Networks for the BN Player.
    :param hidden_suspects: Number of hidden suspect cards, which is the domain size of the variables in
    the suspects BN.
    :param hidden_weapons: Number of hidden weapon cards, which is the domain size of the variables in
    the weapons BN.
    :param hidden_rooms:  Number of hidden room cards, which is the domain size of the variables in
    the rooms BN.
    :return: a tuple (suspects model, weapons model, rooms model)
    """

    # Suspects model:
    suspects_model = BayesianModel([('s', 's1_p2'), ('s', 's2_p2'), ('s1_p2', 's2_p2'), ('s', 's1_p3'),
                                   ('s1_p2', 's1_p3'), ('s2_p2', 's1_p3')])

    s_cpd = TabularCPD(variable='s', variable_card=hidden_suspects, values=create_cpd_table(0, hidden_suspects))
    s1_p2_cpd = TabularCPD(variable='s1_p2', variable_card=hidden_suspects,
                           values=create_cpd_table(1, hidden_suspects),
                           evidence=['s'], evidence_card=[hidden_suspects])
    s2_p2_cpd = TabularCPD(variable='s2_p2', variable_card=hidden_suspects,
                           values=create_cpd_table(2, hidden_suspects),
                           evidence=['s', 's1_p2'], evidence_card=[hidden_suspects, hidden_suspects])
    s1_p3_cpd = TabularCPD(variable='s1_p3', variable_card=hidden_suspects,
                           values=create_cpd_table(3, hidden_suspects),
                           evidence=['s', 's1_p2', 's2_p2'], evidence_card=[hidden_suspects,
                                                                            hidden_suspects, hidden_suspects])
    suspects_model.add_cpds(s_cpd, s1_p2_cpd, s2_p2_cpd, s1_p3_cpd)

    # Weapons model:
    weapons_model = BayesianModel([('w', 'w1_p2'), ('w', 'w2_p2'), ('w', 'w1_p3'), ('w', 'w2_p3'),
                                   ('w1_p2', 'w2_p2'), ('w1_p2', 'w1_p3'), ('w1_p2', 'w2_p3'),
                                   ('w2_p2', 'w1_p3'), ('w2_p2', 'w2_p3'),
                                   ('w1_p3', 'w2_p3')])

    w_cpd = TabularCPD(variable='w', variable_card=hidden_weapons, values=create_cpd_table(0, hidden_weapons))
    w1_p2_cpd = TabularCPD(variable='w1_p2', variable_card=hidden_weapons,
                           values=create_cpd_table(1, hidden_weapons),
                           evidence=['w'], evidence_card=[hidden_weapons])
    w2_p2_cpd = TabularCPD(variable='w2_p2', variable_card=hidden_weapons,
                           values=create_cpd_table(2, hidden_weapons),
                           evidence=['w', 'w1_p2'], evidence_card=[hidden_weapons, hidden_weapons])
    w1_p3_cpd = TabularCPD(variable='w1_p3', variable_card=hidden_weapons,
                           values=create_cpd_table(3, hidden_weapons),
                           evidence=['w', 'w1_p2', 'w2_p2'], evidence_card=[hidden_weapons,
                                                                            hidden_weapons, hidden_weapons])
    w2_p3_cpd = TabularCPD(variable='w2_p3', variable_card=hidden_weapons,
                           values=create_cpd_table(4, hidden_weapons),
                           evidence=['w', 'w1_p2', 'w2_p2', 'w1_p3'], evidence_card=[hidden_weapons, hidden_weapons,
                                                                                     hidden_weapons, hidden_weapons])
    weapons_model.add_cpds(w_cpd, w1_p2_cpd, w2_p2_cpd, w1_p3_cpd, w2_p3_cpd)

    # Rooms model:
    rooms_model = BayesianModel([('r', 'r1_p2'), ('r', 'r2_p2'), ('r', 'r1_p3'), ('r', 'r2_p3'),
                                 ('r1_p2', 'r2_p2'), ('r1_p2', 'r1_p3'), ('r1_p2', 'r2_p3'),
                                 ('r2_p2', 'r1_p3'), ('r2_p2', 'r2_p3'),
                                 ('r1_p3', 'r2_p3')])
    r_cpd = TabularCPD(variable='r', variable_card=hidden_rooms, values=create_cpd_table(0, hidden_rooms))
    r1_p2_cpd = TabularCPD(variable='r1_p2', variable_card=hidden_rooms,
                           values=create_cpd_table(1, hidden_rooms),
                           evidence=['r'], evidence_card=[hidden_rooms])
    r2_p2_cpd = TabularCPD(variable='r2_p2', variable_card=hidden_rooms,
                           values=create_cpd_table(2, hidden_rooms),
                           evidence=['r', 'r1_p2'], evidence_card=[hidden_rooms, hidden_rooms])
    r1_p3_cpd = TabularCPD(variable='r1_p3', variable_card=hidden_rooms,
                           values=create_cpd_table(3, hidden_rooms),
                           evidence=['r', 'r1_p2', 'r2_p2'], evidence_card=[hidden_rooms,
                                                                            hidden_rooms, hidden_rooms])
    r2_p3_cpd = TabularCPD(variable='r2_p3', variable_card=hidden_rooms,
                           values=create_cpd_table(4, hidden_rooms),
                           evidence=['r', 'r1_p2', 'r2_p2', 'r1_p3'], evidence_card=[hidden_rooms, hidden_rooms,
                                                                                     hidden_rooms, hidden_rooms])
    rooms_model.add_cpds(r_cpd, r1_p2_cpd, r2_p2_cpd, r1_p3_cpd, r2_p3_cpd)
    return suspects_model, weapons_model, rooms_model


def normalize_cpd(cpd, most_probable_index):
    cpd.normalize()
    np.nan_to_num(cpd.values, copy=False, nan=1/cpd.values.shape[1])


def nodes_before(node):
    s = ['s', 's1_p2', 's2_p2', 's1_p3']
    w = ['w', 'w1_p2', 'w2_p2', 'w1_p3', 'w2_p3']
    r = ['r', 'r1_p2', 'r2_p2', 'r1_p3', 'r2_p3']
    if node in s:
        return s[:s.index(node)]
    if node in w:
        return w[:w.index(node)]
    if node in r:
        return r[:r.index(node)]


def make_array_sum_to_one(a):
    new = a / np.sum(a)
    new[-1] = 0
    new[-1] = 1 - np.sum(new)
    return new
