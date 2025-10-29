from pydantic import BaseModel, Field
from typing import Literal


class FactsComparisonResultModel(BaseModel):
    result: Literal["ADD", "UPDATE", "NONE"] = Field(default="None", description="The result of the comparison between the old fact and the new fact.")
    fact: str = Field(default="", description="The final fact that is to be stored in the Vector DB.")
