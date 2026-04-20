from typing import TypedDict, List, Dict, Any
from typing_extensions import Annotated
import operator
from pydantic import BaseModel, Field

# The exact JSON structure we want from Ollama
class ArchitecturalFlaw(BaseModel):
    file_name: str
    flaw_type: str = Field(
        description="Must be one of: SRP Violation, Method Doing Too Much, Duplication, Broken Polymorphism, Infra Coupling, Broken Idempotency, Non-Deterministic Output, Context Bloat, Missing Validation, Silent Error, Broken Encapsulation"
    )
    severity: str | None = Field(default=None, description="Critical, High, Medium, Low")
    description: str | None = Field(default=None, description="A concise explanation of how the code violates this specific architectural principle.")
    redacted_code_snippet: str | None = Field(default=None, description="The exact snippet of code, with any fake secrets redacted.")

class FileFindings(BaseModel):
    flaws: List[ArchitecturalFlaw]

class GraphState(TypedDict):
    file_queue: List[str]
    current_file: str | None
    #findings: Annotated[List[Dict[str, Any]], operator.add]
    findings: Annotated[list, operator.add]
    migration_strategy: str
    router_decision: str 
