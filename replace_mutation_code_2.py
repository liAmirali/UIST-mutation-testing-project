import os
from typing import List
from pydantic import BaseModel, Field


class MutationLocation(BaseModel):
    """Represents the location of a mutation in the source code."""
    line_number: int
    start_column: int
    end_column: int


class Mutation(BaseModel):
    """Represents a single mutation in the code."""
    id: str = Field(..., description="Unique identifier for the mutation (e.g., M1, M2)")
    operator: str = Field(..., description="Name of the mutation operator applied")
    mutated_code: str = Field(..., description="Modified code after applying the mutation")
    location: MutationLocation = Field(..., description="Location of the mutation in the source code")
    explanation: str = Field(..., description="Explanation of why and how the code was mutated")


class MutationResult(BaseModel):
    """Represents the complete mutation testing result."""
    total_mutations: int = Field(..., description="Total number of mutations generated")
    mutations: List[Mutation] = Field(..., description="List of all generated mutations")
    applied_operators: List[str] = Field(..., description="List of mutation operators that were applied")


def replace_mutated_classes(folder_path: str, mutation_result: MutationResult):
    """
    Replaces the content of Java classes in the given folder based on the mutations provided.

    Args:
        folder_path (str): Path to the folder containing Java classes.
        mutation_result (MutationResult): The mutations to apply.
    """
    # Iterate over all mutations in the result
    for mutation in mutation_result.mutations:
        mutated_code = mutation.mutated_code
        # Extract the class name from the mutated code
        first_line = mutated_code.splitlines()[0]
        if not first_line.startswith("package"):
            print(f"Could not determine package for mutation {mutation.id}. Skipping.")
            continue

        # Extract the file name from the package path
        package_path = first_line.split("package")[1].strip(";").replace(".", "/")
        class_name = mutated_code.split("class")[1].split()[0].strip("{").strip()
        file_name = f"{class_name}.java"
        file_path = os.path.join(folder_path, package_path, file_name)

        if os.path.exists(file_path):
            # Replace the content of the file with the mutated code
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(mutated_code)
            print(f"Mutation {mutation.id}: Replaced content of {file_path}")
        else:
            print(f"Mutation {mutation.id}: File {file_path} not found. Skipping.")


# Example usage
if __name__ == "__main__":
    # Sample MutationResult instance
    mutation_result = MutationResult(
        total_mutations=2,
        mutations=[
            Mutation(
                id="M1",
                operator="IPC",
                mutated_code="package com.example.apfinalproject.banksystem;\n\n"
                             "...<rest of the mutated code>",
                location=MutationLocation(line_number=52, start_column=9, end_column=59),
                explanation="Removed the call to the superclass constructor in JariAccount."
            ),
            Mutation(
                id="M2",
                operator="PRV",
                mutated_code="package com.example.apfinalproject.banksystem;\n\n"
                             "...<rest of the mutated code>",
                location=MutationLocation(line_number=54, start_column=20, end_column=40),
                explanation="Changed the right side of the assignment to refer to a different ArrayList object."
            )
        ],
        applied_operators=["IPC", "PRV"]
    )

    # Path to the folder containing the Java files
    source_folder = "/path/to/java/source/folder"

    # Apply the mutations
    replace_mutated_classes(source_folder, mutation_result)
