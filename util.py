from enum import Enum
import random
import heapq

RANDOM = "random"
HUMAN = "human"
PLANNING = "planning"
BN2 = "bn2"
BN = "bn"
Character = Enum('Character', 'MissScarlett MrGreen ProfPlum ColonelMustard MrsPeacock MrsWhite')
Weapon = Enum('Weapon', 'Candlestick Dagger LeadPipe Revolver Rope Wrench')
Room = Enum('Room', 'Study Hall Lounge DinningRoom Kitchen BallRoom Conservatory BilliardRoom Library')

CHARACTERS = [character for character in Character]
WEAPONS = [weapon for weapon in Weapon]
ROOMS = [room for room in Room]

PLAYERS_SHORT = {Character.MissScarlett: 'S', Character.ColonelMustard: 'M',
                 Character.MrsPeacock: 'E', Character.MrsWhite: 'W',
                 Character.ProfPlum: 'P', Character.MrGreen: 'G'}

BOARD_SIZE = 25
EDGE_WIDTH = 9  # At least 3
CUBE_SIZE = 12  # Maximum integer result of the cube

# Just try to remove the obstacle:
LOCATIONS = []

for x in range(EDGE_WIDTH):
    for i in [x, BOARD_SIZE - 1 - x]:
        for j in range(BOARD_SIZE):
            LOCATIONS.append((i, j))
            LOCATIONS.append((j, i))

OPEN_LOC = {Character.MissScarlett: (0, int((2 / 3) * BOARD_SIZE)),
            Character.ColonelMustard: (BOARD_SIZE // 3, BOARD_SIZE - 1),
            Character.MrsPeacock: (int((3 / 4) * BOARD_SIZE), 0), Character.ProfPlum: (BOARD_SIZE // 3, 0),
            Character.MrsWhite: (BOARD_SIZE - 1, BOARD_SIZE // 3 * 2),
            Character.MrGreen: (BOARD_SIZE - 1, BOARD_SIZE // 3)}

ROOMS_LOC = {(0, 0): Room.Study, (EDGE_WIDTH - 2, BOARD_SIZE // 2): Room.Hall, (0, BOARD_SIZE - 1): Room.Lounge,
             (BOARD_SIZE // 2, BOARD_SIZE - EDGE_WIDTH + 2): Room.DinningRoom,
             (BOARD_SIZE - 1, BOARD_SIZE - 1): Room.Kitchen,
             (BOARD_SIZE - EDGE_WIDTH + 2, BOARD_SIZE // 2): Room.BallRoom, (BOARD_SIZE - 1, 0): Room.Conservatory,
             (BOARD_SIZE // 3 * 2, EDGE_WIDTH - 4): Room.BilliardRoom, (BOARD_SIZE // 2, EDGE_WIDTH - 3): Room.Library}

LOCATIONS_OF_ROOMS = {Room.Study: (0, 0), Room.Hall: (EDGE_WIDTH - 2, BOARD_SIZE // 2),
                      Room.Lounge: (0, BOARD_SIZE - 1),
                      Room.DinningRoom: (BOARD_SIZE // 2, BOARD_SIZE - EDGE_WIDTH + 2),
                      Room.Kitchen: (BOARD_SIZE - 1, BOARD_SIZE - 1),
                      Room.BallRoom: (BOARD_SIZE - EDGE_WIDTH + 2, BOARD_SIZE // 2),
                      Room.Conservatory: (BOARD_SIZE - 1, 0),
                      Room.BilliardRoom: (BOARD_SIZE // 3 * 2, EDGE_WIDTH - 4),
                      Room.Library: (BOARD_SIZE // 2, EDGE_WIDTH - 3)}


def manhattan_distance(loc1, loc2):
    return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])


class Pair(object):
    """
    A utility class to represent pairs (ordering of the objects in the pair does not matter).
    It is used to represent mutexes (for both actions and propositions)
    """

    def __init__(self, a, b):
        """
        Constructor
        """
        self.a = a
        self.b = b

    def __eq__(self, other):
        if (self.a == other.a) & (self.b == other.b):
            return True
        if (self.b == other.a) & (self.a == other.b):
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "(" + str(self.a) + "," + str(self.b) + ")"

    def __hash__(self):
        return hash(self.a) + hash(self.b)


"""
 Data structures useful for implementing SearchAgents
"""


class Queue:
    """
    A container with a first-in-first-out (FIFO) queuing policy.
    """

    def __init__(self):
        self.list = []

    def push(self, item):
        """
        Enqueue the 'item' into the queue
        """
        self.list.insert(0, item)

    def pop(self):
        """
        Dequeue the earliest enqueued item still in the queue.
        This operation removes the item from the queue.
        """
        if not self.list:
            return
        return self.list.pop()

    def isEmpty(self):
        """
        Returns true if the queue is empty
        """
        return len(self.list) == 0


class PriorityQueue:
    """
    Implements a priority queue data structure. Each inserted item
    has a priority associated with it and the client is usually interested
    in quick retrieval of the lowest-priority item in the queue. This
    data structure allows O(1) access to the lowest-priority item.
    Note that this PriorityQueue does not allow you to change the priority
    of an item.  However, you may insert the same item multiple times with
    different priorities.
    """

    def __init__(self):
        self.heap = []
        self.init = False

    def push(self, item, priority):
        if not self.init:
            self.init = True
            try:
                item < item
            except:
                item.__class__.__lt__ = lambda x, y: True
        pair = (priority, item)
        heapq.heappush(self.heap, pair)

    def pop(self):
        (priority, item) = heapq.heappop(self.heap)
        return item

    def isEmpty(self):
        return len(self.heap) == 0


"""
Data structures and functions useful for various course projects
The search project should not need anything below this line.
"""


class Counter(dict):
    """
    A counter keeps track of counts for a set of keys.
    The counter class is an extension of the standard python
    dictionary type.  It is specialized to have number values
    (integers or floats), and includes a handful of additional
    functions to ease the task of counting data.  In particular,
    all keys are defaulted to have value 0.  Using a dictionary:
    a = {}
    print(a['test'])
    would give an error, while the Counter class analogue:
    >>> a = Counter()
    >>> print(a['test'])
    0
    returns the default 0 value. Note that to reference a key
    that you know is contained in the counter,
    you can still use the dictionary syntax:
    >>> a = Counter()
    >>> a['test'] = 2
    >>> print(a['test'])
    2
    This is very useful for counting things without initializing their counts,
    see for example:
    >>> a['blah'] += 1
    >>> print(a['blah'])
    1
    The counter also includes additional functionality useful in implementing
    the classifiers for this assignment.  Two counters can be added,
    subtracted or multiplied together.  See below for details.  They can
    also be normalized and their total count and arg max can be extracted.
    """

    def __getitem__(self, idx):
        self.setdefault(idx, 0)
        return dict.__getitem__(self, idx)

    def increment_all(self, keys, count):
        """
        Increments all elements of keys by the same count.
        >>> a = Counter()
        >>> a.increment_all(['one','two', 'three'], 1)
        >>> a['one']
        1
        >>> a['two']
        1
        """
        for key in keys:
            self[key] += count

    def arg_max(self):
        """
        Returns the key with the highest value.
        """
        if len(self.keys()) == 0:
            return None
        all_items = list(self.items())
        values = [x[1] for x in all_items]
        max_index = values.index(max(values))
        return all_items[max_index][0]

    def sorted_keys(self):
        """
        Returns a list of keys sorted by their values.  Keys
        with the highest values will appear first.
        >>> a = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> a['third'] = 1
        >>> a.sorted_keys()
        ['second', 'third', 'first']
        """
        sorted_items = list(self.items())
        sorted_items.sort(key=lambda item: -item[1])
        return [x[0] for x in sorted_items]

    def total_count(self):
        """
        Returns the sum of counts for all keys.
        """
        return sum(self.values())

    def normalize(self):
        """
        Edits the counter such that the total count of all
        keys sums to 1.  The ratio of counts for all keys
        will remain the same. Note that normalizing an empty
        Counter will result in an error.
        """
        total = float(self.total_count())
        if total == 0:
            return
        for key in self.keys():
            self[key] = self[key] / total

    def divide_all(self, divisor):
        """
        Divides all counts by divisor
        """
        divisor = float(divisor)
        for key in self:
            self[key] /= divisor

    def copy(self):
        """
        Returns a copy of the counter
        """
        return Counter(dict.copy(self))

    def __mul__(self, y):
        """
        Multiplying two counters gives the dot product of their vectors where
        each unique label is a vector element.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['second'] = 5
        >>> a['third'] = 1.5
        >>> a['fourth'] = 2.5
        >>> a * b
        14
        """
        sum_ = 0
        x = self
        if len(x) > len(y):
            x, y = y, x
        for key in x:
            if key not in y:
                continue
            sum_ += x[key] * y[key]
        return sum_

    def __radd__(self, y):
        """
        Adding another counter to a counter increments the current counter
        by the values stored in the second counter.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> a += b
        >>> a['first']
        1
        """
        for key, value in y.items():
            self[key] += value

    def __add__(self, y):
        """
        Adding two counters gives a counter with the union of all keys and
        counts of the second added to counts of the first.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> (a + b)['first']
        1
        """
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] + y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = y[key]
        return addend

    def __sub__(self, y):
        """
        Subtracting a counter from another gives a counter with the union of all keys and
        counts of the second subtracted from counts of the first.
        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> (a - b)['first']
        -5
        """
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] - y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = -1 * y[key]
        return addend


def normalize(vector_or_counter):
    """
    normalize a vector or counter by dividing each value by the sum of all values
    """
    normalized_counter = Counter()
    if type(vector_or_counter) == type(normalized_counter):
        counter = vector_or_counter
        total = float(counter.total_count())
        if total == 0: return counter
        for key in counter.keys():
            value = counter[key]
            normalized_counter[key] = value / total
        return normalized_counter
    else:
        vector = vector_or_counter
        s = float(sum(vector))
        if s == 0:
            return vector
        return [el / s for el in vector]


def get_probability(value, distribution, values):
    """
      Gives the probability of a value under a discrete distribution
      defined by (distributions, values).
    """
    total = 0.0
    for prob, val in zip(distribution, values):
        if val == value:
            total += prob
    return total


def opposite_side_x_axis(loc1, loc2):
    return is_in_right_side(loc1) and is_in_left_side(loc2) or \
           is_in_right_side(loc2) and is_in_left_side(loc1)


def opposite_side_y_axis(loc1, loc2):
    return is_in_up_side(loc1) and is_in_down_side(loc2) or \
           is_in_up_side(loc2) and is_in_down_side(loc1)


def is_in_right_side(loc):
    return EDGE_WIDTH <= loc[0] < BOARD_SIZE - EDGE_WIDTH <= loc[1]


def is_in_up_side(loc):
    return loc[0] < EDGE_WIDTH <= loc[1] < BOARD_SIZE - EDGE_WIDTH


def is_in_left_side(loc):
    return BOARD_SIZE - EDGE_WIDTH > loc[0] >= EDGE_WIDTH > loc[1]


def is_in_down_side(loc):
    return loc[0] >= BOARD_SIZE - EDGE_WIDTH > loc[1] >= EDGE_WIDTH


def manhattan_distance_with_block(loc1, loc2):
    if opposite_side_x_axis(loc1, loc2):
        min_vertical = min((BOARD_SIZE - EDGE_WIDTH - loc1[0]) + (BOARD_SIZE - EDGE_WIDTH - loc2[0]),
                           (loc1[0] - EDGE_WIDTH + 1) + (loc2[0] - EDGE_WIDTH + 1))
        return min_vertical + abs(loc1[1] - loc2[1])

    if opposite_side_y_axis(loc1, loc2):
        min_vertical = min((BOARD_SIZE - EDGE_WIDTH - loc1[1]) + (BOARD_SIZE - EDGE_WIDTH - loc2[1]),
                           (loc1[1] - EDGE_WIDTH + 1) + (loc2[1] - EDGE_WIDTH + 1))
        return min_vertical + abs(loc1[0] - loc2[0])

    return manhattan_distance(loc1, loc2)
