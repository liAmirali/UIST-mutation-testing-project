import os
import shutil
import glob
import json
from typing import List, Dict, Any, Union
from src.util_classes import MutationResult, Mutation, TestSuiteResult, TestResult, TestClassResult
from src.test_runner import JUnitTestRunner


class MutantTester:
    def __init__(self, original_dir: str, test_dir: str, mutation_dir: str, test_results_dir: str):
        """
        Initialize the JavaMutationHandler.

        Args:
            original_dir (str): Path to the original directory containing Java classes.
        """
        self._original_dir = original_dir
        self._test_dir = test_dir
        self._mutation_dir = mutation_dir
        self._test_results_dir = test_results_dir

        self._test_runner = JUnitTestRunner(self._test_dir, self._test_results_dir)

    def apply_and_test_mutations(self, mutation_results: List[MutationResult]) -> None:
        """
        Apply mutations to Java files and manage the mutation process.

        :param mutation_results: (MutationResult): Object containing mutations and their details.
        """

        for mutation_result in mutation_results:
            for mutation in mutation_result.mutations:
                self._apply_single_mutation(mutation, mutation_result.rel_path)
                # Compile and test the mutated code
                self._test_mutated_source(mutation)

    def read_test_results(self) -> Dict[str, TestSuiteResult]:
        """
        Read test results from the test results directory.
        
        Returns:
            Dict[str, TestSuiteResult]: Dictionary mapping mutant IDs to their test results
        """
        results = {}
        
        # Get all JSON files in the test results directory
        result_files = glob.glob(os.path.join(self._test_results_dir, "*.json"))
        
        for file_path in result_files:
            try:
                # Extract mutant ID from filename (e.g., "M1.json" -> "M1")
                mutant_id = os.path.splitext(os.path.basename(file_path))[0]
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Parse test classes
                test_classes = []
                for class_data in data['test_classes']:
                    # Parse individual test results for this class
                    test_results = [
                        TestResult(
                            test_name=test['test_name'],
                            test_unique_id=test['test_unique_id'],
                            is_passed=test['is_passed'],
                            error_message=test['error_message']
                        )
                        for test in class_data['test_results']
                    ]
                    
                    # Create TestClassResult object
                    class_result = TestClassResult(
                        test_class_name=class_data['test_class_name'],
                        passed_tests=class_data['passed_tests'],
                        failed_tests=class_data['failed_tests'],
                        total_tests=class_data['total_tests'],
                        test_results=test_results
                    )
                    test_classes.append(class_result)
                
                # Create TestSuiteResult object
                suite_result = TestSuiteResult(
                    timestamp=data['timestamp'],
                    test_classes=test_classes,
                    compiled=data['compiled'],
                    compile_error=data.get('compile_error', None)
                )
                
                results[mutant_id] = suite_result
                
            except Exception as e:
                print(f"Error reading test results for {file_path}: {str(e)}")
                continue
        
        return results

    def get_mutation_summary(self, test_results: Dict[str, TestSuiteResult]) -> Dict[str, Any]:
        """
        Generate a summary of mutation testing results.
        
        Args:
            test_results (Dict[str, TestSuiteResult]): The test results from read_test_results()
            
        Returns:
            Dict containing summary statistics:
                - total_mutants: Total number of mutants
                - killed_mutants: Number of mutants that caused test failures
                - survived_mutants: Number of mutants that passed all tests
                - mutation_score: Percentage of mutants killed (killed_mutants/total_mutants)
                - test_impact: Dict mapping test names to number of mutants they killed
        """
        total_mutants = len(test_results)
        killed_mutants = 0
        survived_mutants = 0
        test_impact = {}  # Track which tests kill which mutants
        
        for mutant_id, suite_result in test_results.items():
            # Check if any test failed for this mutant
            mutant_killed = False
            
            for test_class in suite_result.test_classes:
                for test_result in test_class.test_results:
                    test_key = f"{test_class.test_class_name}#{test_result.test_name}"
                    
                    if not test_result.is_passed:
                        mutant_killed = True
                        # Increment counter for this test
                        test_impact[test_key] = test_impact.get(test_key, 0) + 1
            
            if mutant_killed:
                killed_mutants += 1
            else:
                survived_mutants += 1
        
        mutation_score = (killed_mutants / total_mutants * 100) if total_mutants > 0 else 0
        
        return {
            "total_mutants": total_mutants,
            "killed_mutants": killed_mutants,
            "survived_mutants": survived_mutants,
            "mutation_score": mutation_score,
            "test_impact": test_impact
        }

    def _apply_single_mutation(self, mutation: Mutation, rel_path: str) -> None:
        """
        Apply a single mutation to the appropriate Java file.

        Args:
            mutation: Single mutation object containing mutation details.
        """
        # Make sure this is the path in the original folder
        mutant_dir = os.path.join(self._mutation_dir, mutation.id)

        # Copy original source code to mutant_dir
        shutil.copytree(self._original_dir, mutant_dir)

        file_path = os.path.join(mutant_dir, rel_path)
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as java_file:
                java_file.write(mutation.mutated_code)
        else:
            print(f"Class {file_path} not found in: {self._original_dir}")

    def _revert_mutant_file(self, rel_path: str) -> None:
        """
        Revert the mutated Java file back to its original state.
        """

        # Copy the original file back to the mutation directory
        original_file_path = os.path.join(self._original_dir, rel_path)
        mutated_file_path = os.path.join(self._mutation_dir, rel_path)

        shutil.copyfile(original_file_path, mutated_file_path)

    def _test_mutated_source(self, mutation: Mutation) -> None:
        """
        Test the mutated Java source code.

        Args:
            mutation (Mutation): Single mutation object containing mutation details.
        """

        mutant_src_dir = os.path.join(self._mutation_dir, mutation.id)
        mutant_build_src_dir = os.path.join(mutant_src_dir, "build")
        
        self._test_runner.run_test_runner(src_dir=mutant_src_dir, build_dir=mutant_build_src_dir, test_result_filename=mutation.id)

    @staticmethod
    def get_class_name_from_code(code: str) -> Union[str | None]:
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

    def find_java_file(self, class_name: str) -> Union[str | None]:
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
