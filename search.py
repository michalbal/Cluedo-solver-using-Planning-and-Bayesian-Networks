"""
In search.py, you will implement generic search algorithms
"""

import util


class SearchProblem:
    """
    This class outlines the structure of a search problem, but doesn't implement
    any of the methods (in object-oriented terminology: an abstract class).

    You do not need to change anything in this class, ever.
    """

    def get_start_state(self):
        """
        Returns the start state for the search problem
        """
        util.raiseNotDefined()

    def is_goal_state(self, state):
        """
        state: Search state

        Returns True if and only if the state is a valid goal state
        """
        util.raiseNotDefined()

    def get_successors(self, state):
        """
        state: Search state

        For a given state, this should return a list of triples,
        (successor, action, stepCost), where 'successor' is a
        successor to the current state, 'action' is the action
        required to get there, and 'stepCost' is the incremental
        cost of expanding to that successor
        """
        util.raiseNotDefined()

    def get_cost_of_actions(self, actions):
        """
        actions: A list of actions to take

        This method returns the total cost of a particular sequence of actions.  The sequence must
        be composed of legal moves
        """
        util.raiseNotDefined()


class Node:
    def __init__(self, state, cost, path, asked_before, location=None, action=None,
                 this_question=None):
        self.state = state
        self.cost = cost
        if location:
            self.location = location
        self.asked_before = dict()
        # save the last asked question
        for q in asked_before:
            self.asked_before[q] = asked_before[q]

        self.last_question = this_question
        if action is not None:
            self.path = path + [action]
            if this_question:
                # All previous question - doesn't matter at the end of the plan
                for q in this_question:
                    if q in asked_before:
                        self.asked_before[q] += 1
                    else:
                        self.asked_before[q] = 1
                self.location = util.LOCATIONS_OF_ROOMS[util.Room[this_question[2]]]
        else:
            self.path = path


def a_star_search(problem, heuristic, location):
    """
    Search the node that has the lowest combined cost and heuristic first.
    """
    fringe = util.PriorityQueue()
    visited = set()
    first_state = problem.get_start_state()
    fringe.push(Node(first_state, 0, [], dict(), location), 0)
    while not fringe.isEmpty():
        current_node = fringe.pop()
        if current_node.state not in visited:
            if problem.is_goal_state(current_node.state):
                return current_node.path
            # Expand node
            visited.add(current_node.state)
            successors = problem.get_successors(current_node.state)
            asked_before = current_node.asked_before
            current_location = current_node.location
            for succ, action, cost in successors:
                this_question, result = None, None
                if "unknown" in action.name:
                    name = action.name.split("_unknown_")
                    this_question = name[0:3]
                accumulated_cost = current_node.cost + cost
                heuristic_cost = heuristic(asked_before, this_question, succ,
                                           current_location, problem)
                fringe.push(
                    Node(succ, accumulated_cost, current_node.path, asked_before,
                         current_location, action, this_question),
                    accumulated_cost + heuristic_cost)
    return None

