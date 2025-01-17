import subprocess
import os
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path
from typing import List, Union
import logging

class JUnitTestRunner:
    def __init__(self, src_dir: str, test_dir: str, jar_files_dir: str):
        """
        Initialize the JUnit test runner
        
        Args:
            src_dir (str): Path to source code directory
            test_dir (str): Path to test code directory
            jar_files_dir (str): Path to all the JAR files required for compilation and testing
            hamcrest_jar_path (str): Path to hamcrest-core.jar
        """
        self.src_dir = Path(src_dir)
        self.test_dir = Path(test_dir)
        self.jar_files_dir = Path(jar_files_dir)
        self.build_dir = Path("build")
        self.results_dir = Path("test-results")

        self._logger = logging.getLogger(__name__)
        
    def prepare_directories(self):
        """Create necessary directories if they don't exist"""
        self.build_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    def _create_classpath(self, include_build: bool = False):
        """Creates the classpath string"""

        all_files_to_include = []
        if include_build:
            all_files_to_include.append(self.build_dir)
        
        for jar_file in self.jar_files_dir.glob("*.jar"):
            all_files_to_include.append(jar_file)

        if os.name == 'nt':  # Windows
            sep = ";"
        else:  # Unix-based systems
            sep = ":"
        
        classpath = sep.join([str(f) for f in all_files_to_include])

        return classpath
        
    def compile_code(self):
        """Compile both source and test code"""
        # Compile source files
        src_files = list(self.src_dir.glob("**/*.java"))
        test_files = list(self.test_dir.glob("**/*.java"))
        
        classpath = self._create_classpath()

        self._logger.info(f"Compiling source files: {src_files}")
        self._logger.info(f"Compiling test files: {test_files}")

        self._logger.debug(f"Classpath:", classpath)

        # Compile source files
        compile_cmd = [
            "javac",
            "-d", str(self.build_dir),
            "-cp", classpath
        ] + [str(f) for f in src_files + test_files]
        
        result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Compilation failed:\n{result.stderr}")
            
    def run_tests(self):
        """Run JUnit tests and return results"""
        # Find all test classes
        test_classes = []
        for file in self.test_dir.glob("**/*Test.java"):
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
        
        subprocess.run(cmd, capture_output=True, text=True)

    def save_results(self, results):
        """Save test results to JSON and generate JUnit XML report"""
        # Save JSON results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = self.results_dir / f"test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        # Generate JUnit XML report
        xml_file = self.results_dir / f"TEST-results_{timestamp}.xml"
        root = ET.Element("testsuites")
        
        for result in results:
            testsuite = ET.SubElement(root, "testsuite")
            testsuite.set("name", result["class"])
            testsuite.set("timestamp", result["timestamp"])
            
            # Parse the output to get individual test results
            for line in result["output"].split('\n'):
                if line.startswith("Test"):
                    testcase = ET.SubElement(testsuite, "testcase")
                    testcase.set("name", line.split()[1])
                    if "FAILED" in line:
                        failure = ET.SubElement(testcase, "failure")
                        failure.text = line
            
        tree = ET.ElementTree(root)
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        
        return str(json_file), str(xml_file)

if __name__ == "__main__":
    runner = JUnitTestRunner(
        src_dir="./mutant-runner/src/main",
        test_dir="./mutant-runner/src/test",
        jar_files_dir="./lib",
    )

    logging.getLogger(__name__).setLevel(logging.DEBUG)

    try:
        runner.prepare_directories()
        runner.compile_code()
        runner.run_tests()
        # json_file, xml_file = runner.save_results(results)
        # print(f"Results saved to:\nJSON: {json_file}\nXML: {xml_file}")
    except Exception as e:
        print(f"Error: {e}")