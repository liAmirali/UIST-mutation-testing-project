from typing import List, Optional

from dataclasses import dataclass
from pydantic import BaseModel, Field

# Mutations
@dataclass
class MutationLocation:
    """Represents the location of a mutation in the source code"""
    line_number: int
    start_column: Optional[int] = None
    end_column: Optional[int] = None

class Mutation(BaseModel):
    """Represents a single mutation in the code"""
    id: str = Field(..., description="Unique identifier for the mutation (e.g., M1, M2)")
    operator: str = Field(..., description="Name of the mutation operator applied")
    mutated_code: str = Field(..., description="Modified code after applying the mutation")
    location: MutationLocation = Field(..., description="Location of the mutation in the source code")
    explanation: str = Field(..., description="Explanation of why and how the code was mutated")

class MutationResult(BaseModel):
    """Represents the complete mutation testing result"""
    rel_path: str = Field(..., description="Relative path to the file where the mutation was applied from the original directory")
    total_mutations: int = Field(..., description="Total number of mutations generated")
    mutations: List[Mutation] = Field(..., description="List of all generated mutations")

class MutationOperatorSelection(BaseModel):
    """Represents a mutation operator selection"""
    operator_name: str = Field(..., description="Name of the mutation operator selected")
    reason: str = Field(..., description="Explanation of why this operator was selected")


# Test results
@dataclass
class TestResult:
    test_name: str
    test_unique_id: str
    is_passed: bool
    error_message: str

@dataclass
class TestClassResult:
    test_class_name: str
    passed_tests: int
    failed_tests: int
    total_tests: int
    test_results: List[TestResult]

@dataclass
class TestSuiteResult:
    timestamp: str
    test_classes: List[TestClassResult]
    compiled: bool
    compile_error: Optional[str] = None

