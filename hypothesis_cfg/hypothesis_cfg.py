from math import exp
from hypothesis.strategies import composite, builds, randoms, sampled_from
import random

from utils import Nonterminal, NonterminalCollection, Terminal, Expansion


def get_cfg_string(cfg_file_path: str) -> str:
    try:
        with open(cfg_file_path, "r") as f:
            cfg = f.read()
        return cfg
    except FileNotFoundError:
        print(f"File not found: {cfg_file_path}")
        return ""


# needs to be make more robust and be less restrictive
# maybe check fuzzing book to see if they have a better parser
def parse_cfg(
    cfg_string: str,
) -> NonterminalCollection:
    """
    Takes in CFG's defined with the following format:
    S is the start symbol
    Nonterminals are enclosed in <> (reserved characters)
    Expansions are defined with :=
    Alternatives are separated by |
    Nonterminals must be defined in a single line
    Terminals are not enclosed
    """

    nonterminals = NonterminalCollection()
    expansions = {}

    def parse_expansion(
        expansion_string: str,
    ) -> Expansion:
        expansion = Expansion()
        current_string = None
        for char in expansion_string:
            if char == "<":
                if current_string is not None:
                    expansion.add_part(Terminal(current_string))
                    current_string = None
            elif char == ">":
                if current_string is not None:
                    nonterminals.add_nonterminal(
                        Nonterminal(current_string, expansions)
                    )
                    expansion.add_part(nonterminals[current_string])
                    current_string = None
            else:
                if current_string is None:
                    current_string = ""
                current_string += char
        if current_string is not None:
            expansion.add_part(Terminal(current_string))
        return expansion

    for line in cfg_string.split("\n"):
        if line == "":
            continue

        line = line.split(":=")
        nonterminal_string = line[0].strip()
        if nonterminal_string not in nonterminals:
            nonterminals.add_nonterminal(Nonterminal(nonterminal_string, expansions))

        for expansion in line[1].strip().split("|"):
            nonterminals[nonterminal_string].add_expansion(parse_expansion(expansion))

    return nonterminals


def get_min_distances(
    nonterminals: NonterminalCollection,
) -> tuple[list[Nonterminal], int | float]:
    """
    Takes in a NonterminalCollection and returns a tuple with a list of
    unreachable nonterminals and the minimum required depth to reach a terminal
    from the start symbol
    """

    # pass over every nonterminal and check if it has a terminal, set its min distance to 1 and add it to a frontier with distance 1
    for nonterminal in nonterminals:
        for expansion in nonterminal.get_expansions():
            if expansion.produces_only_terminals():
                nonterminal.set_min_distance_to_terminal(1)
                break

    # Bellman Ford to get the min distances to terminals for each nonterminal
    for _ in range(len(nonterminals)):
        for nonterminal in nonterminals:
            for expansion in nonterminal.get_expansions():
                new_min_distance = expansion.get_min_distance_to_terminal()
                if new_min_distance < nonterminal.get_min_distance_to_terminal():
                    nonterminal.set_min_distance_to_terminal(new_min_distance)

    # get unreachable nonterminals and min required depth to reach a terminal from the start symbol
    unreachable_nonterminals = [
        nonterminal
        for nonterminal in nonterminals
        if nonterminal.is_currently_unreachable()
    ]
    reachable_nonterminal_distances = [
        nonterminal.get_min_distance_to_terminal()
        for nonterminal in nonterminals
        if nonterminal.get_min_distance_to_terminal() != float("inf")
    ]
    min_required_depth = (
        max(reachable_nonterminal_distances)
        if reachable_nonterminal_distances
        else float("inf")
    )

    return unreachable_nonterminals, min_required_depth


# @composite
def generate_string(
    nonterminals: NonterminalCollection,
    max_depth: int,
) -> str:
    """
    Generates strings from a CFG defined by a NonterminalCollection.
    Limit search to strings derivable with a max depth using algorithm from class.
    """

    start_symbol = nonterminals["S"]
    remaining_depth = max_depth

    # maybe use a custom parse tree class to make the expansions easier
    current_string = [start_symbol]
    next_nonterminal = start_symbol

    while remaining_depth >= 0 and next_nonterminal != [None]:
        potential_expansions = next_nonterminal.get_expansions()  # type: ignore
        valid_expansions = []
        for expansion in potential_expansions:
            expansion_depth = expansion.get_min_distance_to_terminal()
            if expansion_depth <= remaining_depth:
                valid_expansions.append(expansion)

        print(f"valid_expansions: {valid_expansions}")
        expansion = random.choice(valid_expansions)
        # expansion = draw(sampled_from(valid_expansions))
        print(f"current string: {current_string}, chose expansion: {expansion}")

        current_string = (
            current_string[: current_string.index(next_nonterminal)]
            + expansion.to_list()
            + current_string[current_string.index(next_nonterminal) + 1 :]
        )
        print(f"current string: {current_string}")

        remaining_depth -= 1
        # use default value of next_nonterminal=[None] to break loop if no nonterminal is found
        next_nonterminal = next(
            (part for part in current_string if isinstance(part, Nonterminal)), [None]
        )
        print(f"next_nonterminal: {next_nonterminal}")

    return "".join([str(part) for part in current_string])


@composite
def cfg(draw, cfg_file_path: str = "", max_depth: int | None = None):

    # open file
    print(f"cfg_file_path: {cfg_file_path}")
    cfg_string = get_cfg_string(cfg_file_path)
    print(f"cfg_string: {cfg_string}")
    if cfg_string == "":
        return ""

    # parse file and get grammar in python classes
    nonterminals = parse_cfg(cfg_string)
    print(f"nonterminals: {nonterminals}")
    for nonterminal in nonterminals:
        print(f"{nonterminal} expansions: {nonterminal.get_expansions()}")

    # graph exploration to label min distances to terminals
    unreachable_nonterminals, min_required_depth = get_min_distances(nonterminals)
    print(f"unreachable_detected: {unreachable_nonterminals}")
    for nonterminal in nonterminals:
        print(
            f"{nonterminal} min_distance_to_terminal: {nonterminal.get_min_distance_to_terminal()}"
        )
    if unreachable_nonterminals:
        print(
            "WARNING: There are unreachable nonterminals:",
            [nonterminal for nonterminal in unreachable_nonterminals],
        )
    if max_depth is not None and max_depth < min_required_depth:
        print(
            f"WARNING: max_depth ({max_depth}) is too low. Minimum required depth to reach a terminal is {min_required_depth}."
        )

    # generate random string from grammar w/ max depths
    depth = (
        max_depth
        if max_depth is not None
        else min_required_depth if min_required_depth != float("inf") else 10
    )
    result = generate_string(nonterminals, depth)  # type: ignore
    print(f"generated: {result}")

    return result
    # return draw(result)
