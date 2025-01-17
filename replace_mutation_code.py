import os
import shutil

from src.output_classes import MutationResult, Mutation
from src.test_runner import JUnitTestRunner

class MutantTester:
    def __init__(self, original_dir: str, test_dir: str,  mutation_result: MutationResult):
        """
        Initialize the JavaMutationHandler.

        Args:
            original_dir (str): Path to the original directory containing Java classes.
            mutation_result (MutationResult): Object containing mutations and their details.
        """
        self._original_dir = original_dir
        self._test_dir = test_dir
        self._mutation_dir = original_dir + "_mutated"
        self._mutation_result = mutation_result

        self._test_runner = JUnitTestRunner(self._mutation_dir, self._test_dir)

    def apply_and_test_mutations(self) -> None:
        """
        Apply mutations to Java files and manage the mutation process.

        Args:
            mutation_result (MutationResult): Object containing mutations and their details.
        """

        self._init_mutation_dir()

        for mutation in self._mutation_result.mutations:
            try:
                self._apply_single_mutation(mutation)
                # Compile and test the mutated code
                self._test_mutated_source(mutation)
            finally:
                self._revert_mutant_file()

    def _init_mutation_dir(self) -> str:
        """
        Create a temporary directory with copied contents from original directory.

        Returns:
            str: Path to the temporary directory.
        """

        # Remove the existing mutation directory if it exists
        if os.path.exists(self._mutation_dir):
            shutil.rmtree(self._mutation_dir)

        # Initialize the mutation directory with the original source code
        shutil.copytree(self._original_dir, self._mutation_dir)

    def _apply_single_mutation(self, mutation: Mutation) -> None:
        """
        Apply a single mutation to the appropriate Java file.

        Args:
            mutation: Single mutation object containing mutation details.
        """
        # Make sure this is the path in the original folder
        file_path = mutation.path
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as java_file:
                java_file.write(mutation.mutated_code)
        else:
            print(f"Class {file_path} not found in: {self._original_dir}")

    def _revert_mutant_file(self, mutation: Mutation) -> None:
        """
        Revert the mutated Java file back to its original state.
        """
        file_path = mutation.path
        if file_path:
            
            # Copy the original file back to the mutation directory
            original_file_path = os.path.join(self._original_dir, file_path)
            mutated_file_path = os.path.join(self._mutation_dir, file_path)

            shutil.copyfile(original_file_path, mutated_file_path)

    def _test_mutated_source(self, mutation: Mutation) -> None:
        """
        Test the mutated Java source code.

        Args:
            mutated_source (str): Mutated Java source code.
        """
        
        self._test_runner.run_test_runner(result_filename=mutation.id)

    @staticmethod
    def get_class_name_from_code(code: str) -> str:
        """
        Extract the class name from the Java code.

        Args:
            code (str): Java code.

        Returns:
            str: Class name if found, None otherwise.
        """
        for line in code.splitlines():
            line = line.strip()
            if line.startswith("public class ") or line.startswith("class "):
                return line.split()[2].strip("{")
        return None

    def find_java_file(self, class_name: str) -> str:
        """
        Find the file path of a Java class in the folder.

        Args:
            class_name (str): Name of the class to find.

        Returns:
            str: Path to the Java file if found, None otherwise.
        """
        for root, _, files in os.walk(self._original_dir):
            for file in files:
                if file == f"{class_name}.java":
                    return os.path.join(root, file)
        return None


def main():
    """Example usage of the JavaMutationHandler class."""
    original_folder = "path/to/java/classes/folder"
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

    handler = MutantTester(original_folder)
    mutation_result = MutationResult(**mutation_data)
    handler.apply_and_test_mutations(mutation_result)


if __name__ == "__main__":
    main()