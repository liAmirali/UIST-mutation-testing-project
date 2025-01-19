import os
import shutil
import glob
import json
from enum import Enum
from typing import List, Dict, Any, Union, Optional
import logging
from src.util_classes import MutationResult, Mutation, TestSuiteResult, TestResult, TestClassResult
from src.test_runner import JUnitTestRunner

ORIGINAL_SRC_TEST_RESULTS_NAME = "original"

class MutantStatus(Enum):
    LIVE = "live"
    KILLED = "killed"
    STILLBORN = "stillborn"
    TRIVIAL = "trivial"

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

        self._logger = logging.getLogger(__name__)

    def test_original_code(self) -> None:
        """
        Test the original Java source code.
        """
        self._test_runner.run_test_runner(src_dir=self._original_dir, build_dir=os.path.join(self._original_dir, "build"), test_result_filename=ORIGINAL_SRC_TEST_RESULTS_NAME)

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
                            error_message=test.get('error_message', None)
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
                self._logger.error(f"Error reading test results from {file_path}: {e}")
                continue
        
        return results

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
            self._logger.error(f"Class {file_path} not found in: {self._original_dir}")

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


    def _evaluate_mutant(self, mutation_id: str, test_results: Dict[str, TestSuiteResult]) -> MutantStatus:
        """
        Evaluate the status of a single mutant based on test results.
        A mutant is killed if any test behaves differently than it did on the original code.

        Args:
            mutation (Mutation): The mutation to evaluate
            test_results (Dict[str, TestSuiteResult]): Dictionary of all test results

        Returns:
            MutantStatus: The status of the mutant (LIVE, KILLED, STILLBORN, or TRIVIAL)
        """
        self._logger.debug(f"Evaluating mutant {mutation_id}")

        # Get test results for this mutant
        mutant_results = test_results.get(mutation_id)
        if not mutant_results:
            self._logger.error(f"Test results not found for mutant {mutation_id} -> STILLBORN")
            return MutantStatus.STILLBORN

        # Check if mutant compiled
        if not mutant_results.compiled:
            self._logger.error(f"Mutant {mutation_id} failed to compile -> STILLBORN")
            return MutantStatus.STILLBORN

        # Get original test results for comparison
        original_results = test_results.get(ORIGINAL_SRC_TEST_RESULTS_NAME)
        if not original_results:
            raise ValueError("Original test results not found")

        different_results = 0
        total_tests = 0
        
        # Compare each test result with original
        for mutant_class in mutant_results.test_classes:
            self._logger.debug(f"Checking mutant class: {mutant_class}")

            # Find corresponding original class results
            original_class = next(
                (c for c in original_results.test_classes 
                 if c.test_class_name == mutant_class.test_class_name),
                None
            )

            if not original_class:
                self._logger.error(f"Original class not found for mutant class {mutant_class.test_class_name}")
                continue
            
            self._logger.debug(f"Found original class: {original_class}")

            for mutant_test in mutant_class.test_results:
                self._logger.debug(f"Checking mutant test: {mutant_test}")

                # Find corresponding original test result
                original_test = next(
                    (t for t in original_class.test_results 
                     if t.test_unique_id == mutant_test.test_unique_id),
                    None
                )

                self._logger.debug(f"Found original test: {original_test}")
                
                if not original_test:
                    self._logger.error(f"Original test not found for mutant test {mutant_test.test_name}")
                    continue

                total_tests += 1
                # If test result is different from original, count it
                if mutant_test.is_passed != original_test.is_passed:
                    self._logger.debug(f"Test {mutant_test.test_name} differs from original: [Original:{original_test.is_passed} -> Mutant:{mutant_test.is_passed}")
                    different_results += 1

        # Determine mutant status
        if different_results == 0:
            self._logger.debug(f"Mutant {mutation_id} is LIVE")
            return MutantStatus.LIVE
        elif different_results == total_tests:
            self._logger.debug(f"Mutant {mutation_id} is TRIVIAL")
            return MutantStatus.TRIVIAL
        else:
            self._logger.debug(f"Mutant {mutation_id} is KILLED")
            return MutantStatus.KILLED

    def get_mutation_summary(self, test_results: Dict[str, TestSuiteResult]) -> Dict[str, Any]:
        """
        Generate a summary of mutation testing results.
        
        Args:
            test_results (Dict[str, TestSuiteResult]): The test results from read_test_results()
            
        Returns:
            Dict containing summary statistics:
                - total_mutants: Total number of mutants
                - mutant_status_counts: Count of mutants by status (live, killed, stillborn, trivial)
                - mutation_score: Percentage of mutants killed
                - test_impact: Dict mapping test names to number of mutants they killed
                - mutation_status: Dict mapping mutant IDs to their status
        """
        total_mutants = len(test_results) - 1  # Subtract 1 to exclude original results
        status_counts = {status: 0 for status in MutantStatus}
        test_impact = {}
        mutation_status = {}

        # Process each mutant
        for mutant_id, suite_result in test_results.items():
            # Skip the original source code test results
            if mutant_id == ORIGINAL_SRC_TEST_RESULTS_NAME:
                continue
            
            # Evaluate mutant status
            status = self._evaluate_mutant(mutant_id, test_results)
            status_counts[status] += 1
            mutation_status[mutant_id] = status.value

            # Track test impact for killed mutants
            if status in [MutantStatus.KILLED, MutantStatus.TRIVIAL]:
                for test_class in suite_result.test_classes:
                    for test_result in test_class.test_results:
                        if not test_result.is_passed:
                            test_key = f"{test_class.test_class_name}#{test_result.test_name}"
                            test_impact[test_key] = test_impact.get(test_key, 0) + 1

        print("test impact:", test_impact)
        print("mutation status:", mutation_status)

        killed_total = status_counts[MutantStatus.KILLED]
        stillborn_total = status_counts[MutantStatus.STILLBORN]
        effective_mutants = total_mutants - stillborn_total
        mutation_score = (killed_total / (effective_mutants)) * 100 if effective_mutants > 0 else 0

        return {
            "total_mutants": total_mutants,
            "mutant_status_counts": {
                "live": status_counts[MutantStatus.LIVE],
                "killed": status_counts[MutantStatus.KILLED],
                "stillborn": status_counts[MutantStatus.STILLBORN],
                "trivial": status_counts[MutantStatus.TRIVIAL]
            },
            "mutation_score": mutation_score,
            "test_impact": test_impact,
            "mutation_status": mutation_status
        }