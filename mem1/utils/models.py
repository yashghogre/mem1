from pydantic import BaseModel, Field
from typing import List, Literal


class FactsComparisonResultModel(BaseModel):
    result: Literal["ADD", "UPDATE", "NONE"] = Field(default="None", description="The result of the comparison between the old fact and the new fact.")
    fact: str = Field(default="", description="The final fact that is to be stored in the Vector DB.")


class GraphTriplets(BaseModel):
    subject: str
    predicate: str
    object: str
    subject_type: str = Field(description="Type of the subject, e.g., Person, Location, Concept", default="Entity")
    object_type: str = Field(description="Type of the object, e.g., Person, Location, Concept", default="Entity")


class KnowledgeGraphExtraction(BaseModel):
    triplets: List[GraphTriplets]
