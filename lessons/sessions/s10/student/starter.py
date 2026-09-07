"""S10: test the boundary around one goal."""


def at_goal(count, goal):
    # TODO: only after recording all three predictions, replace False.
    return False


goal = 3

# TODO: after the comparison is revealed, add assertions for goal - 1, goal,
# and goal + 1.
print(at_goal(goal - 1, goal))
print(at_goal(goal, goal))
print(at_goal(goal + 1, goal))
