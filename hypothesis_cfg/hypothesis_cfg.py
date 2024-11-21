from math import exp
from sre_parse import WHITESPACE
from string import whitespace
from turtle import mode
from hypothesis.strategies import composite, builds, randoms, sampled_from
import random

from utils import (
    NONTERMINAL_FIRST_CHAR,
    NONTERMINAL_REMAINING_CHARS,
    CharacterCollector,
    Nonterminal,
    NonterminalCollection,
    Terminal,
    Expansion,
    Modes,
)


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
    Terminals are enclosed in '' (single quotes)
    Expansions are defined with :=
    Alternatives are separated by |
    Nonterminal definitions are separated by an empty line
    Nonterminals definitions can span multiple lines but cannot have an empty line in the middle of a definition
        ^ may break if we need to define a nonterminal which has multiple consecutive newlines
    """

    nonterminals = NonterminalCollection()
    expansions = {}

    mode = Modes.FIND_DECLARATION
    current_string = CharacterCollector()
    for char in cfg_string:
        match mode:
            case Modes.FIND_DECLARATION:
                match char:
                    case whitespace if char in WHITESPACE:
                        continue
                    case char if char in NONTERMINAL_FIRST_CHAR:
                        mode = Modes.GET_DECLARATION
                        current_string.start()
                        current_string.add_char(char)
                    case _:
                        raise ValueError(f"Invalid character: {char}")
            case Modes.GET_DECLARATION:
                match char:
                    case char if char in NONTERMINAL_REMAINING_CHARS:
                        current_string.add_char(char)
                    case char if char in WHITESPACE or char == "|":
                        nonterminal_string = current_string.get_str()
                        nonterminals.add_nonterminal(
                            Nonterminal(nonterminal_string, expansions)
                        )
                        expansion.add_part(nonterminals[nonterminal_string])  # type: ignore because we just added it
                        mode = Modes.EXPANSION
            case Modes.FIND_ASSIGNMENT:
                match char:
                    case whitespace if char in WHITESPACE:
                        continue
                    case ":":
                        mode = Modes.GET_ASSIGNMENT
                    case _:
                        raise ValueError(f"Invalid character: {char}")
            case Modes.GET_ASSIGNMENT:
                match char:
                    case "=":
                        mode = Modes.EXPANSION
                    case _:
                        raise ValueError(f"Invalid character: {char}")
            case Modes.EXPANSION:
                expansion = Expansion()
                # current_string = None
                current_mode = Modes.NONE
                for char in expansion_string:
                    match current_mode:
                        case Modes.NONE:
                            match char:
                                case "'":
                                    current_mode = Modes.TERMINAL
                                    # current_string = ""
                                case "<":
                                    current_mode = Modes.NONTERMINAL
                                    # current_string = ""
                                case " " | "\n" | "\t":
                                    continue
                                case _:
                                    raise ValueError(f"Invalid character: {char}")
                        case Modes.TERMINAL:
                            match char:
                                case "'":
                                    expansion.add_part(Terminal(current_string))
                                    current_mode = Modes.NONE
                                    # current_string = None
                                case "\\":
                                    current_mode = Modes.BACKSLASH
                                case _:
                                    pass
                                    # current_string += char  # type: ignore bc current_string should be str by NONE case
                        case Modes.NONTERMINAL:
                            match char:
                                case ">":
                                    nonterminals.add_nonterminal(
                                        Nonterminal(current_string, expansions)
                                    )
                                    expansion.add_part(nonterminals[current_string])  # type: ignore because we just added it
                                    current_mode = Modes.NONE
                                    # current_string = None
                                case _:
                                    pass
                                    # current_string += char  # type: ignore bc current_string should be str by NONE case
                        case Modes.BACKSLASH:
                            # current_string += eval(f"'\\{char}'")  # type: ignore bc current_string should be str by NONE case
                            current_mode = Modes.TERMINAL

                nonterminals[nonterminal_string].add_expansion(expansion)

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
        if nonterminal.get_min_distance_to_terminal() != Nonterminal.infinity
    ]
    min_required_depth = (
        max(reachable_nonterminal_distances)
        if reachable_nonterminal_distances
        else Nonterminal.infinity
    )

    return unreachable_nonterminals, min_required_depth


# @composite
def generate_string(
    start_part: Nonterminal | Terminal,
    max_depth: int,
) -> str:
    """
    Recursively generates strings from a CFG defined by a NonterminalCollection.
    Limit search to strings derivable with a max depth using algorithm from class.
    """

    # base case: terminal node - return the terminal
    if isinstance(start_part, Terminal):
        print("terminal node: ", start_part)
        return start_part.get_terminal()

    # recursive case: nonterminal node - get a list of all expansions
    print("next nonterminal node: ", start_part)
    potential_expansions: list[Expansion] = start_part.get_expansions()

    # filter out expansions that are too deep
    valid_expansions = [
        expansion
        for expansion in potential_expansions
        if expansion.get_min_distance_to_terminal() <= max_depth
    ]
    print(f"valid_expansions: {valid_expansions}")

    # choose a random valid expansion
    expansion = random.choice(valid_expansions)
    # expansion = draw(sampled_from(valid_expansions))
    print(f"chosen_expansion: {expansion}")

    # recurse on all children and concatenate the results
    result = "".join(
        generate_string(child, max_depth - 1) for child in expansion.get_expansion()
    )

    return result


@composite
def cfg(draw, cfg_file_path: str = "", max_depth: int | None = None):

    # open file
    print(f"cfg_file_path: {cfg_file_path}")
    cfg_string = get_cfg_string(cfg_file_path)
    print(f"cfg_string:\n{cfg_string}")
    if cfg_string == "":
        return ""

    # parse file and get grammar in python classes
    print()
    nonterminals = parse_cfg(cfg_string)
    print(f"nonterminals: {nonterminals}")
    for nonterminal in nonterminals:
        print(f"{nonterminal} expansions: {nonterminal.get_expansions()}")

    # graph exploration to label min distances to terminals
    print()
    unreachable_nonterminals, min_required_depth = get_min_distances(nonterminals)
    print(f"unreachable_nonterminals: {unreachable_nonterminals}")
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
    print()
    depth = (
        max_depth
        if max_depth is not None
        else min_required_depth * 2 if min_required_depth < Nonterminal.infinity else 10
    )
    print(f"max_depth: {depth}")
    result = generate_string(nonterminals["S"], depth)  # type: ignore
    print(f"generated: {result}")

    return result
    # return draw(result)
