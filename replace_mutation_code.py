import os
import shutil
from pydantic import BaseModel, Field
from typing import List


class MutationLocation(BaseModel):
    """Represents the location of a mutation in the source code"""
    line_number: int
    start_column: int
    end_column: int


class Mutation(BaseModel):
    """Represents a single mutation in the code"""
    id: str = Field(..., description="Unique identifier for the mutation (e.g., M1, M2)")
    operator: str = Field(..., description="Name of the mutation operator applied")
    mutated_code: str = Field(..., description="Modified code after applying the mutation")
    location: MutationLocation = Field(..., description="Location of the mutation in the source code")
    explanation: str = Field(..., description="Explanation of why and how the code was mutated")


class MutationResult(BaseModel):
    """Represents the complete mutation testing result"""
    total_mutations: int = Field(..., description="Total number of mutations generated")
    mutations: List[Mutation] = Field(..., description="List of all generated mutations")
    applied_operators: List[str] = Field(..., description="List of mutation operators that were applied")


def replace_mutated_files(original_folder: str, mutation_result: MutationResult):
    """
    Replace the content of Java classes affected by mutations with their mutated code.

    Args:
        original_folder (str): Path to the original folder containing Java classes.
        mutation_result (MutationResult): Object containing mutations and their details.
    """
    for mutation in mutation_result.mutations:
        # Create a copy of the original folder for this mutation
        temp_folder = f"{original_folder}_temp"
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        shutil.copytree(original_folder, temp_folder)

        # Make sure this is the path in the original folder
        file_path = "F1/Test.java"
        if file_path:
            # Replace the content of the file with the mutated code
            with open(file_path, 'w', encoding='utf-8') as java_file:
                java_file.write(mutation.mutated_code)
            print(f"Applied mutation {mutation.id} to {file_path}")
        else:
            print(f"Class {file_path} not found: {original_folder}")

        # Process the temporary folder (e.g., run tests here if needed)
        # ...


        shutil.move(temp_folder, original_folder)

        # Clean up the temporary folder after processing
        shutil.rmtree(temp_folder)


def get_class_name_from_code(code: str) -> str:
    """
    Extract the class name from the Java code.

    Args:
        code (str): Java code.

    Returns:
        str: Class name.
    """
    for line in code.splitlines():
        line = line.strip()
        if line.startswith("public class ") or line.startswith("class "):
            return line.split()[2].strip("{")
    return None


def find_java_file(folder_path: str, class_name: str) -> str:
    """
    Find the file path of a Java class in the folder.

    Args:
        folder_path (str): Path to the folder containing Java classes.
        class_name (str): Name of the class to find.

    Returns:
        str: Path to the Java file if found, otherwise None.
    """
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file == f"{class_name}.java":
                return os.path.join(root, file)
    return None


# Example usage
if __name__ == "__main__":
    original_folder = "path/to/java/classes/folder"  # Replace with the path to your original folder
    mutation_data = {
        "total_mutations": 2,
        "mutations": [
            {
                "id": "M1",
                "operator": "IPC",
                "mutated_code": """<Insert mutated code for class 1>""",
                "location": {"line_number": 52, "start_column": 9, "end_column": 59},
                "explanation": "Removed the call to the superclass constructor in JariAccount."
            },
            {
                "id": "M2",
                "operator": "PRV",
                "mutated_code": """<Insert mutated code for class 2>""",
                "location": {"line_number": 54, "start_column": 20, "end_column": 40},
                "explanation": "Changed the right side of the assignment to refer to a different ArrayList object."
            }
        ],
        "applied_operators": ["IPC", "PRV"]
    }

    mutation_result = MutationResult(**mutation_data)
    replace_mutated_files(original_folder, mutation_result)
