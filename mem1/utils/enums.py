from enum import StrEnum


class NoFactStrings(StrEnum):
    NONE = "None"
    NO_PREV_FACT = "No previous facts"


class FactComparisonResult(StrEnum):
    ADD = "ADD"
    UPDATE = "UPDATE"
    NONE = "NONE"

