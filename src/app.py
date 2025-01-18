from src.vector_store import VectorStore
from src.operator_selector import OperatorSelector
from src.mutation_assistant import MutationAssistant
from src.mutant_tester import MutantTester

from src.util_classes import MutationResult

from typing import List

import os
import shutil

DOCS_JSON_PATH = "./docs.json"
PROJECTS_DIR = "./projects"

class App:
    def init(self, project_name: str, source_code_path: str, test_code_path: str):
        """
        Initialize the application with the given project name.

        Args:
            project_name (str): Name of the project.
        """

        if self._check_project_name_exists(project_name):
            raise ValueError(f"Project name '{project_name}' already exists in the configuration file.")
        
        self._source_code_path = source_code_path
        self._test_code_path = test_code_path

        self._project_root_dir = PROJECTS_DIR / project_name
        self._project_original_src_dir = self._project_root_dir / "original_src"
        self._project_tests_dir = self._project_root_dir / "tests"
        self._project_mutations_dir = self._project_root_dir / "mutations"
        self._project_test_results_dir = self._project_root_dir / "test_results"

        self._prepare_project_dirs()

        vector_store = VectorStore()
        docs = vector_store.load_documents_json(DOCS_JSON_PATH)
        store = vector_store.create_vector_store(docs)

        self.operator_selector = OperatorSelector(store)
        self.mutation_assistant = MutationAssistant(store)
        self.mutant_tester = MutantTester()

    def _check_project_name_exists(self, project_name: str) -> bool:
        """
        Check if the project name already exists in the configuration file.

        Args:
            project_name (str): Name of the project to check.

        Returns:
            bool: True if the project name exists, False otherwise.
        """
        
        # Check existing folder name in the PROJECTS_DIR
        return os.path.exists(PROJECTS_DIR / project_name)

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
        shutil.copytree(self._source_code_path, self._project_original_src_dir)
        # Copy the test code to the tests directory
        shutil.copytree(self._test_code_path, self._project_tests_dir)

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

        for source_file in self._project_original_src_dir.glob("**/*.java"):
            with open(source_file, 'r') as file:
                source_code = file.read()

            # TODO: Retrieve other helping source codes

            mutation_result, _ = self.mutation_assistant.generate(source_code=source_code, mutation_operators=operator_names)
            mutation_results.append(mutation_result)
        
        return mutation_results
            
    def get_file_relpath(self, file_path: str):
        """
        Get the relative path of the file.
        """
        return os.path.relpath(file_path, self.app._project_original_src_dir)