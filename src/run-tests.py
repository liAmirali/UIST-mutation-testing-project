import subprocess
import os
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path
from typing import List, Union
import logging

class JUnitTestRunner:
    def __init__(self, src_dir: str, test_dir: str, junit_jar_path: str, hamcrest_jar_path: str):
        """
        Initialize the JUnit test runner
        
        Args:
            src_dir (str): Path to source code directory
            test_dir (str): Path to test code directory
            junit_jar_path (str): Path to junit.jar
            hamcrest_jar_path (str): Path to hamcrest-core.jar
        """
        self.src_dir = Path(src_dir)
        self.test_dir = Path(test_dir)
        self.junit_jar = Path(junit_jar_path)
        self.hamcrest_jar = Path(hamcrest_jar_path)
        self.build_dir = Path("build")
        self.results_dir = Path("test-results")

        self._logger = logging.getLogger(__name__)
        
    def prepare_directories(self):
        """Create necessary directories if they don't exist"""
        self.build_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    def _create_classpath(self, jar_files: List[Union[str, Path]]):
        """Creates the classpath string based on the OS"""
        if os.name == 'nt':  # Windows
            classpath = ";".join([str(f) for f in jar_files])
        else:  # Unix-based systems
            classpath = ":".join([str(f) for f in jar_files])
        return classpath
        
    def compile_code(self):
        """Compile both source and test code"""
        # Compile source files
        src_files = list(self.src_dir.glob("**/*.java"))
        test_files = list(self.test_dir.glob("**/*.java"))
        
        classpath = self._create_classpath([self.junit_jar, self.hamcrest_jar, self.build_dir])

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
            # Convert file path to class name
            class_name = str(file.relative_to(self.test_dir))
            class_name = class_name.replace('/', '.').replace('\\', '.')[:-5]  # Remove .java
            test_classes.append(class_name)
        
        # Run tests
        classpath = self._create_classpath([self.junit_jar, self.hamcrest_jar, self.build_dir])
        results = []
        
        for test_class in test_classes:
            cmd = [
                "java",
                "-cp", classpath,
                "org.junit.runner.JUnitCore",
                test_class
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)

            print(result)
            
            # Parse the output
            test_result = {
                "class": test_class,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            results.append(test_result)
            
        return results

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
        src_dir="./java_example_projects/university_management_system/src",
        test_dir="./java_example_projects/university_management_system/test",
        junit_jar_path="./lib/junit-platform-console-standalone-1.11.4.jar",
        hamcrest_jar_path="./lib/hamcrest-3.0.jar",
    )

    logging.getLogger(__name__).setLevel(logging.DEBUG)

    try:
        runner.prepare_directories()
        runner.compile_code()
        results = runner.run_tests()
        json_file, xml_file = runner.save_results(results)
        print(f"Results saved to:\nJSON: {json_file}\nXML: {xml_file}")
    except Exception as e:
        print(f"Error: {e}")