from src.vector_store import VectorStore
from src.operator_selector import OperatorSelector
from src.mutation_assistant import MutationAssistant
from src.mutant_tester import MutantTester

from src.util_classes import MutationResult, TestSuiteResult

from typing import List, Tuple, Dict

from pathlib import Path
import os
import shutil

DOCS_JSON_PATH = "./docs.json"
PROJECTS_DIR = "./projects"

class App:
    def init(self, project_name: str, source_code_path: str, test_code_path: str):
        """
        Initialize the application with the given project name.


        :param project_name:
        :param test_code_path:
        :param source_code_path:
        """

        if self._check_project_name_exists(project_name):
            raise ValueError(f"Project name '{project_name}' already exists.")
        
        self._source_code_path = source_code_path
        self._test_code_path = test_code_path

        self._project_root_dir = os.path.join(PROJECTS_DIR, project_name)
        self._project_original_src_dir = os.path.join(self._project_root_dir, "original_src")
        self._project_tests_dir = os.path.join(self._project_root_dir, "tests")
        self._project_mutations_dir = os.path.join(self._project_root_dir, "mutations")
        self._project_test_results_dir = os.path.join(self._project_root_dir, "test_results")

        self._prepare_project_dirs()

        vector_store = VectorStore()
        docs = vector_store.load_documents_json(DOCS_JSON_PATH)
        store = vector_store.create_vector_store(docs)

        self.operator_selector = OperatorSelector(store)
        self.mutation_assistant = MutationAssistant(store)
        self.mutant_tester = MutantTester(
            original_dir=self._project_original_src_dir,
            test_dir=self._project_tests_dir,
            mutation_dir=self._project_mutations_dir,
            test_results_dir=self._project_test_results_dir
        )

    def _check_project_name_exists(self, project_name: str) -> bool:
        """
        Check if the project name already exists in the configuration file.

        Args:
            project_name (str): Name of the project to check.

        Returns:
            bool: True if the project name exists, False otherwise.
        """
        
        # Check existing folder name in the PROJECTS_DIR
        return os.path.exists(os.path.join(PROJECTS_DIR, project_name)  )

    def _prepare_project_dirs(self):
        """
        Prepare the project directories.
        """
        os.makedirs(self._project_root_dir, exist_ok=True)
        os.makedirs(self._project_original_src_dir, exist_ok=True)
        os.makedirs(self._project_tests_dir, exist_ok=True)
        os.makedirs(self._project_mutations_dir, exist_ok=True)
        os.makedirs(self._project_test_results_dir, exist_ok=True)

        # Copy the source code to the original source directory
        for item in os.listdir(self._source_code_path):
            s = os.path.join(self._source_code_path, item)
            d = os.path.join(self._project_original_src_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        
        # Copy the test code to the tests directory
        for item in os.listdir(self._test_code_path):
            s = os.path.join(self._test_code_path, item)
            d = os.path.join(self._project_tests_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    def generate_operator_selection(self, user_prompt: str):
        """
        Generate the mutation operator selection.
        """

        selections, _ = self.operator_selector.generate(user_prompt)
        self._selected_operators = selections

        return selections

    def generate_mutations(self) -> List[MutationResult]: 
        """
        Generate mutations based on the selected operators.
        """

        operator_names = [op.operator_name for op in self._selected_operators]

        mutation_results = []

        for source_file in Path(self._project_original_src_dir).glob("**/*.java"):
            with open(source_file, 'r') as file:
                source_code = file.read()

            # TODO: Retrieve other helping source codes

            try:
                mutation_result, _ = self.mutation_assistant.generate(
                    source_code=source_code,
                    mutation_operators=operator_names,
                    mutant_filepath=str(source_file.relative_to(self._project_original_src_dir))
                )
                mutation_results.append(mutation_result)
            except:
                continue
        
        return mutation_results
    
    def run_mutant_tester(self, mutation_results: List[MutationResult]):
        """
        Run the mutant tester on the generated mutations.
        """

        self.mutant_tester.apply_and_test_mutations(mutation_results)

    def get_test_results(self) -> Tuple[Dict[str, TestSuiteResult], Dict]:
        """
        Get the test results and their summary for the project.
        """

        test_results = self.mutant_tester.read_test_results()
        summary = self.mutant_tester.get_mutation_summary(test_results)

        return test_results, summary
            
    def get_file_relpath(self, file_path: str):
        """
        Get the relative path of the file.
        """
        return os.path.relpath(file_path, self._project_original_src_dir)

    def get_original_source_code_path(self, file_rel_path: str) -> str:
        return os.path.join(self._project_original_src_dir, file_rel_path)

    def read_file_content(self, file_path: str):
        """
        Read the content of the file.
        """
        with open(file_path, 'r') as file:
            return file.read()