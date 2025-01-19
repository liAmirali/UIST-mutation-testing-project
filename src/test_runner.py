import subprocess
import os
import shutil
import json
from pathlib import Path
import logging
from datetime import datetime
class JUnitTestRunner:
    def __init__(self, test_dir: str, test_results_dir: str):
        """
        Initialize the JUnit test runner
        
        Args:
            src_dir (str): Path to source code directory
            test_dir (str): Path to test code directory
        """

        self._test_dir = Path(test_dir)
        self._jar_files_dir = Path("./lib")
        self._test_results_dir = Path(test_results_dir)

        self._logger = logging.getLogger(__name__)
        
    def _prepare_directories(self):
        """Create necessary directories if they don't exist"""
        self._build_dir.mkdir(exist_ok=True)
        self._test_results_dir.mkdir(exist_ok=True)

    def _create_classpath(self):
        """Creates the classpath string"""

        all_files_to_include = []
        
        for jar_file in self._jar_files_dir.glob("*.jar"):
            all_files_to_include.append(jar_file)
        
        classpath = os.pathsep.join([str(f) for f in all_files_to_include])

        return classpath
        
    def _compile_code(self, src_dir: str, build_dir: str):
        """Compile both source and test code"""
        # Compile source files
        src_files = list(Path(src_dir).glob("**/*.java"))
        test_files = list(self._test_dir.glob("**/*.java"))
        
        classpath = self._create_classpath()

        self._logger.info(f"Compiling source files: {src_files}")
        self._logger.info(f"Compiling test files: {test_files}")

        # Compile source files
        compile_cmd = [
            "javac",
            "-d", build_dir,
            "-cp", classpath
        ] + [str(f) for f in src_files + test_files]
        
        result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Compilation failed:\n{result.stderr}")
            
    def run_test_runner(self, src_dir: str, build_dir: str, test_result_filename: str):
        """Run JUnit tests and return results"""
        try:
            self._compile_code(src_dir, build_dir)
        except Exception as e:
            self._logger.error(f"Compilation failed: {e}")
            
            # Creating a file to indicate that the test execution failed
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_data = {
                "timestamp": timestamp,
                "compiled": False,
                "test_classes": [],
                "compile_error": f"Compilation failed: {str(e)}"
            }
            
            with open(self._test_results_dir / f"{test_result_filename}.json", "w") as f:
                json.dump(error_data, f)
            
            return

        # Find all test classes
        test_classes = []
        for file in self._test_dir.glob("**/*Test.java"):
            test_classes.append(file.stem)
        
        # Run tests
        classpath = self._create_classpath()

        # Appending the test runner class to the classpath
        classpath += f"{os.pathsep}java-test-runner"

        # Appending the compiled classes to the classpath
        classpath += f"{os.pathsep}{build_dir}"

        print("test_classes:", test_classes)

        cmd = [
            "java",
            "-cp", classpath,
            "TestRunner",  # Custom test runner class bytecode
            *test_classes
        ]
        
        # If the test runner runs with no errors, a file named "test_results.json" will be created
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Test execution failed:\n{result.stderr}")

        # Move the test results file to the results directory
        shutil.move("test_results.json", self._test_results_dir / f"{test_result_filename}.json")

        self._logger.debug(f"Test results file created: {self._test_results_dir / f'{test_result_filename}.json'}")
