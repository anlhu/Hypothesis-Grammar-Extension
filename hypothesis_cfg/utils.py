from enum import Enum
from pickle import GET
from sre_parse import WHITESPACE
import string

WHITESPACE = string.whitespace
ALPHABET = string.ascii_letters
DIGITS = string.digits

NONTERMINAL_FIRST_CHAR = ALPHABET
NONTERMINAL_REMAINING_CHARS = ALPHABET + DIGITS + "_"


class Nonterminal:
    infinity = float("inf")

    def __init__(self, nonterminal, expansions) -> None:
        self._nonterminal = nonterminal
        self._expansions = expansions
        self._min_distance_to_terminal = self.infinity

        if self.get_nonterminal() not in self._expansions:
            self._expansions[self.get_nonterminal()] = []

    def get_nonterminal(self):
        return self._nonterminal

    def get_min_distance_to_terminal(self) -> float:
        return self._min_distance_to_terminal

    def is_currently_unreachable(self) -> bool:
        return self._min_distance_to_terminal == self.infinity

    def set_min_distance_to_terminal(self, min_distance_to_terminal):
        self._min_distance_to_terminal = min_distance_to_terminal

    def get_expansions(self) -> list:
        return (
            self._expansions[self.get_nonterminal()]
            if self.get_nonterminal() in self._expansions
            else []
        )

    def add_expansion(self, expansion):
        self._expansions[self.get_nonterminal()].append(expansion)

    def __repr__(self) -> str:
        return f"<{self._nonterminal}>"

    def __hash__(self) -> int:
        return hash(self._nonterminal)


class Terminal:
    def __init__(self, terminal) -> None:
        self._terminal = terminal

    def get_terminal(self):
        return self._terminal

    def __repr__(self) -> str:
        return f"{self._terminal}"


class Expansion:
    def __init__(self) -> None:
        self._expansion = []

    def get_expansion(self):
        return self._expansion

    def add_part(self, part: Terminal | Nonterminal):
        self._expansion.append(part)

    def produces_only_terminals(self):
        return all(isinstance(part, Terminal) for part in self._expansion)

    def get_min_distance_to_terminal(self):
        return max(
            (
                part.get_min_distance_to_terminal() + 1
                if isinstance(part, Nonterminal)
                else 1
            )
            for part in self._expansion
        )

    def to_list(self):
        return self.get_expansion()

    def __repr__(self) -> str:
        return " ".join(map(str, self._expansion))


class NonterminalCollection:
    def __init__(self):
        self._nonterminals: dict[str, Nonterminal] = {}

    def add_nonterminal(self, nonterminal: Nonterminal):
        if nonterminal.get_nonterminal() not in self._nonterminals:
            self._nonterminals[nonterminal.get_nonterminal()] = nonterminal

    def get_nonterminal(self, nonterminal: str) -> Nonterminal:
        return self._nonterminals[nonterminal]

    def __iter__(self):
        return iter(self._nonterminals.values())

    def __contains__(self, nonterminal: str | Nonterminal) -> bool:
        if isinstance(nonterminal, Nonterminal):
            return nonterminal in self._nonterminals.values()
        elif isinstance(nonterminal, str):
            return nonterminal in self._nonterminals
        print("NonterminalCollection __contains__ got unexpected type")

    def __getitem__(self, nonterminal: str) -> Nonterminal:
        return self._nonterminals[nonterminal]

    def __repr__(self) -> str:

        return str(self._nonterminals)

    def __len__(self) -> int:
        return len(self._nonterminals)


class _Expansion(Enum):
    NONE = 0
    TERMINAL = 1
    NONTERMINAL = 2
    BACKSLASH = 3


class Modes(Enum):
    FIND_DECLARATION = 0
    GET_DECLARATION = 1
    FIND_ASSIGNMENT = 2
    GET_ASSIGNMENT = 3
    EXPANSION = _Expansion


class CharacterCollector:
    def __init__(self) -> None:
        self.str = None

    def start(self):
        if self.str is not None:
            raise ValueError("CharacterCollector already started")
        self.str = ""

    def add_char(self, char):
        self.str += char

    def get_str(self):
        string = self.str
        self.str = None
        return string
