import subprocess
import os
import shutil
from pathlib import Path
import logging

class JUnitTestRunner:
    def __init__(self, src_dir: str, test_dir: str):
        """
        Initialize the JUnit test runner
        
        Args:
            src_dir (str): Path to source code directory
            test_dir (str): Path to test code directory
            jar_files_dir (str): Path to all the JAR files required for compilation and testing
        """
        self._src_dir = Path(src_dir)
        self._test_dir = Path(test_dir)
        self._jar_files_dir = Path("./lib")
        self._build_dir = Path("build")
        self._results_dir = Path("test-results")

        self._logger = logging.getLogger(__name__)
        
    def _prepare_directories(self):
        """Create necessary directories if they don't exist"""
        self._build_dir.mkdir(exist_ok=True)
        self._results_dir.mkdir(exist_ok=True)

    def _create_classpath(self, include_build: bool = False):
        """Creates the classpath string"""

        all_files_to_include = []
        if include_build:
            all_files_to_include.append(self._build_dir)
        
        for jar_file in self._jar_files_dir.glob("*.jar"):
            all_files_to_include.append(jar_file)

        if os.name == 'nt':  # Windows
            sep = ";"
        else:  # Unix-based systems
            sep = ":"
        
        classpath = sep.join([str(f) for f in all_files_to_include])

        return classpath
        
    def _compile_code(self):
        """Compile both source and test code"""
        # Compile source files
        src_files = list(self._src_dir.glob("**/*.java"))
        test_files = list(self._test_dir.glob("**/*.java"))
        
        classpath = self._create_classpath()

        self._logger.info(f"Compiling source files: {src_files}")
        self._logger.info(f"Compiling test files: {test_files}")

        self._logger.debug(f"Classpath:", classpath)

        # Compile source files
        compile_cmd = [
            "javac",
            "-d", str(self._build_dir),
            "-cp", classpath
        ] + [str(f) for f in src_files + test_files]
        
        result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Compilation failed:\n{result.stderr}")
            
    def run_test_runner(self, result_filename: str = None):
        """Run JUnit tests and return results"""
        # Find all test classes
        test_classes = []
        for file in self._test_dir.glob("**/*Test.java"):
            test_classes.append(file.stem)
        
        # Run tests
        classpath = self._create_classpath(include_build=True)

        print("test_classes:", test_classes)

        cmd = [
            "java",
            "-cp", classpath,
            "TestRunner",  # Custom test runner class bytecode
            *test_classes
        ]
        
        # If the test runner runs with no errors, a file named "test_results.json" will be created
        subprocess.run(cmd, capture_output=True, text=True)

        # Move the test results file to the results directory
        shutil.move("test_results.json", self._results_dir / "test_results.json")

        # Rename the file if a custom name was provided
        if result_filename is not None:
            os.rename(self._results_dir / "test_results.json", self._results_dir / f"{result_filename}.json")

if __name__ == "__main__":
    runner = JUnitTestRunner(
        src_dir="./dev-junit-runner/src/main",
        test_dir="./dev-junit-runner/src/test",
        jar_files_dir="./lib",
    )

    logging.getLogger(__name__).setLevel(logging.DEBUG)

    try:
        runner._prepare_directories()
        runner._compile_code()
        runner.run_test_runner()

    except Exception as e:
        print(f"Error: {e}")