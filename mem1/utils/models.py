from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal


class Message(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: Literal["system", "user", "assistant"]
    content: str


class CandidateFactsModel(BaseModel):
    reasoning: str = Field(
        ...,
        description="A brief explanation of why specific facts were extracted or why the list is empty (e.g., 'User only exchanged pleasantries').",
    )
    facts: List[str] = Field(
        default_factory=list,
        description="A list of distinct, atomic facts about the user's goals, preferences, or state. Empty list if no new facts.",
    )


class FactsComparisonResultModel(BaseModel):
    result: Literal["ADD", "UPDATE", "NONE"] = Field(
        default="None",
        description="The result of the comparison between the old fact and the new fact.",
    )
    fact: str = Field(
        default="", description="The final fact that is to be stored in the Vector DB."
    )


class GraphTriplets(BaseModel):
    subject: str
    predicate: str
    object: str
    subject_type: str = Field(
        description="Type of the subject, e.g., Person, Location, Concept",
        default="Entity",
    )
    object_type: str = Field(
        description="Type of the object, e.g., Person, Location, Concept",
        default="Entity",
    )


class KnowledgeGraphExtraction(BaseModel):
    triplets: List[GraphTriplets]
