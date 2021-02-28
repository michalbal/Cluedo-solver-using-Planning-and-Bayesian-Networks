import util
from util import Pair
import copy
from proposition_layer import PropositionLayer
from plan_graph_level import PlanGraphLevel
from pgparser import PgParser
from action import Action

from search import SearchProblem
from search import a_star_search


class PlanningProblem:
    def __init__(self, domain_file, problem_file):
        """
        Constructor
        """
        p = PgParser(domain_file, problem_file)
        self.actions, self.propositions = p.parse_actions_and_propositions()
        # list of all the actions and list of all the propositions

        initial_state, goal = p.parse_problem()
        # the initial state and the goal state are lists of propositions
        self.initialState = frozenset(initial_state)
        self.goal = frozenset(goal)
        for g in goal:
            if "found" not in g.name:
                self.goal_loc = util.LOCATIONS_OF_ROOMS[util.Room[g.name]]
                break
        self.create_noops()
        # creates noOps that are used to propagate existing propositions from one layer to the next

        PlanGraphLevel.set_actions(self.actions)
        PlanGraphLevel.set_props(self.propositions)
        self.expanded = 0

    def get_start_state(self):
        "*** YOUR CODE HERE ***"
        return self.initialState

    def is_goal_state(self, state):
        """
        Hint: you might want to take a look at goal_state_not_in_prop_payer function
        """
        "*** YOUR CODE HERE ***"
        return not self.goal_state_not_in_prop_layer(state)

    def get_successors(self, state):
        """
        For a given state, this should return a list of triples,
        (successor, action, step_cost), where 'successor' is a
        successor to the current state, 'action' is the action
        required to get there, and 'step_cost' is the incremental
        cost of expanding to that successor, 1 in our case.
        You might want to this function:
        For a list / set of propositions l and action a,
        a.all_preconds_in_list(l) returns true if the preconditions of a are in l

        Note that a state *must* be hashable!! Therefore, you might want to represent a state as a frozenset
        """
        self.expanded += 1
        "*** YOUR CODE HERE ***"
        all_successors = []
        for act in self.actions:
            if act.all_preconds_in_list(state) and not act.is_noop():
                successor = set(act.get_add()).union(set(state))
                successor = frozenset(successor.difference(act.get_delete()))
                all_successors.append((successor, act, 1))
        return all_successors

    @staticmethod
    def get_cost_of_actions(actions):
        return len(actions)

    def goal_state_not_in_prop_layer(self, propositions):
        """
        Helper function that receives a  list of propositions (propositions) and returns False
        if not all the goal propositions are in that list
        """
        for goal in self.goal:
            if goal not in propositions:
                return True
        return False

    def create_noops(self):
        """
        Creates the noOps that are used to propagate propositions from one layer to the next
        """
        for prop in self.propositions:
            name = prop.name
            precon = []
            add = []
            precon.append(prop)
            add.append(prop)
            delete = []
            act = Action(name, precon, add, delete, True)
            self.actions.append(act)


def max_level(state, planning_problem):
    """
    The heuristic value is the number of layers required to expand all goal propositions.
    If the goal is not reachable from the state your heuristic should return float('inf')
    A good place to start would be:
    prop_layer_init = PropositionLayer()          #create a new proposition layer
    for prop in state:
        prop_layer_init.add_proposition(prop)        #update the proposition layer with the propositions of the state
    pg_init = PlanGraphLevel()                   #create a new plan graph level (level is the action layer and the propositions layer)
    pg_init.set_proposition_layer(prop_layer_init)   #update the new plan graph level with the the proposition layer
    """
    "*** YOUR CODE HERE ***"
    prop_layer_init = PropositionLayer()  # create a new proposition layer
    for prop in state:
        prop_layer_init.add_proposition(prop)
    graph_layer = PlanGraphLevel()
    graph_layer.set_proposition_layer(prop_layer_init)

    graph = [graph_layer]
    lvl_number = 0
    while True:
        # check if reached goal
        if planning_problem.is_goal_state(graph[-1].get_proposition_layer().get_propositions()):
            return lvl_number
        # check if we are stuck
        if is_fixed(graph, lvl_number):
            return float('inf')
        # otherwise, expand
        new_layer = PlanGraphLevel()
        new_layer.expand_without_mutex(graph[-1])
        graph.append(new_layer)
        lvl_number += 1


def level_sum(state, planning_problem):
    """
    The heuristic value is the sum of sub-goals level they first appeared.
    If the goal is not reachable from the state your heuristic should return float('inf')
    """
    "*** YOUR CODE HERE ***"
    prop_layer_init = PropositionLayer()  # create a new proposition layer
    for prop in state:
        prop_layer_init.add_proposition(prop)
    graph_layer = PlanGraphLevel()
    graph_layer.set_proposition_layer(prop_layer_init)

    graph = [graph_layer]
    sum_of_subgoals = 0
    subgoals = list(planning_problem.goal)
    while True:
        this_lvl = len(graph) - 1
        propositions = graph[-1].get_proposition_layer().get_propositions()
        for pr in propositions:
            if pr in subgoals:
                sum_of_subgoals += this_lvl
                subgoals.remove(pr)
        # check if we are done
        if len(subgoals) == 0:
            return sum_of_subgoals
        # check if we are stuck
        if is_fixed(graph, len(graph) - 1):
            return float('inf')
        # otherwise, expand
        new_layer = PlanGraphLevel()
        new_layer.expand_without_mutex(graph[-1])
        graph.append(new_layer)


def is_fixed(graph, level):
    """
    Checks if we have reached a fixed point,
    i.e. each level we'll expand would be the same, thus no point in continuing
    """
    if level == 0:
        return False
    return len(graph[level].get_proposition_layer().get_propositions()) == len(
        graph[level - 1].get_proposition_layer().get_propositions())


def null_heuristic(*args, **kwargs):
    return 0


def repetition_heuristic(asked_before, this_question, state, current_location,
                         problem):
    if not this_question:
        return 0

    if len(current_location) != 2:
        current_location = util.LOCATIONS_OF_ROOMS[util.Room[current_location]]
    succ_loc = util.LOCATIONS_OF_ROOMS[util.Room[this_question[2]]]

    cost = util.manhattan_distance_with_block(problem.goal_loc, succ_loc) + \
           util.manhattan_distance_with_block(current_location, succ_loc)

    for q in asked_before:
        if q in this_question:
            cost += 5 * (asked_before[q] + 1)
        else:
            cost += 5 * asked_before[q]
    return cost
