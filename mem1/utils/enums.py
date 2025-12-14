from enum import StrEnum


class NoFactStrings(StrEnum):
    NONE = "None"
    NO_PREV_FACT = "No previous facts"


class FactComparisonResult(StrEnum):
    ADD = "ADD"
    UPDATE = "UPDATE"
    NONE = "NONE"


class EntityType(StrEnum):
    PERSON = "Person"
    LOCATION = "Location"
    ORGANIZATION = "Org"
    EVENT = "Event"
    PROJECT = "Project"
    CONCEPT = "Concept"  # For abstract ideas (e.g. "Python", "AI")
    TOOL = "Tool"  # For software/hardware
    MISC = "Misc"
