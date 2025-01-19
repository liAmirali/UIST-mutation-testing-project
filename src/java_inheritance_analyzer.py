import javalang
import networkx as nx
from typing import Dict, List, Optional, Tuple, Any
import os
from pathlib import Path

class JavaInheritanceAnalyzer:
    def __init__(self, source_path: str):
        """
        Initialize the analyzer with a source path, build the class map and inheritance tree.
        
        Args:
            source_path: Path to the Java source code directory
        """
        self.source_path = source_path
        self.inheritance_graph = nx.DiGraph()
        # Maps class names to their file paths. If multiple classes exist in one file,
        # each class name will point to the same file path
        self.class_file_map: Dict[str, str] = {}
        self.class_nodes: Dict[str, javalang.tree.ClassDeclaration] = {}
        self.interface_nodes: Dict[str, javalang.tree.InterfaceDeclaration] = {}
        
        # Initialize everything at once
        self._process_source_directory()

    def _process_source_directory(self) -> None:
        """
        Walks through the source directory, processes all Java files,
        builds the class map and inheritance tree.
        """
        for root, _, files in os.walk(self.source_path):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            source_code = f.read()
                            self._process_java_file(source_code, file_path)
                    except (IOError, javalang.parser.JavaSyntaxError) as e:
                        print(f"Error processing file {file_path}: {e}")

    def _process_java_file(self, source_code: str, file_path: str) -> None:
        """
        Processes a single Java file, updating both the class map and inheritance tree.
        
        Args:
            source_code: Content of the Java file
            file_path: Path to the Java file
        """
        try:
            tree = javalang.parse.parse(source_code)
        except javalang.parser.JavaSyntaxError as e:
            print(f"Error parsing Java code in {file_path}: {e}")
            return

        # Process classes and interfaces
        for _, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
                self.class_file_map[class_name] = file_path
                self.class_nodes[class_name] = node
                self.inheritance_graph.add_node(class_name)
                
                # Add inheritance relationships
                if node.extends:
                    self.inheritance_graph.add_edge(node.extends.name, class_name)
                
                if node.implements:
                    for implemented in node.implements:
                        self.inheritance_graph.add_edge(implemented.name, class_name)
                        
            elif isinstance(node, javalang.tree.InterfaceDeclaration):
                interface_name = node.name
                self.class_file_map[interface_name] = file_path
                self.interface_nodes[interface_name] = node
                self.inheritance_graph.add_node(interface_name)
                
                # Add interface inheritance
                if node.extends:
                    for extended in node.extends:
                        self.inheritance_graph.add_edge(extended.name, interface_name)

    def get_class_relations(self, class_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the parent, siblings, and first-level children of a given class.

        Args:
            class_name: The name of the class for which to retrieve relations.

        Returns:
            A dictionary containing the parent, siblings, and children, or None if the class is not found.
        """
        if class_name not in self.inheritance_graph.nodes:
            return None

        parent_list: List[str] = list(self.inheritance_graph.predecessors(class_name))
        parent: Optional[str] = parent_list[0] if parent_list else None

        siblings: List[str] = []
        if parent:
            for child in self.inheritance_graph.successors(parent):
                if child != class_name:
                    siblings.append(child)

        children: List[str] = list(self.inheritance_graph.successors(class_name))

        return {
            "parent": parent,
            "siblings": siblings,
            "children": children
        }

    def extract_class_names_from_source(self, source_code: str) -> List[str]:
        """
        Extracts all class and interface names from a given source code snippet.

        Args:
            source_code: The source code snippet as a string.

        Returns:
            A list of class/interface names found in the source code.
        """
        class_names = []
        try:
            tree = javalang.parse.parse(source_code)
            for _, node in tree:
                if isinstance(node, (javalang.tree.ClassDeclaration, 
                                  javalang.tree.InterfaceDeclaration)):
                    class_names.append(node.name)
            return class_names
        except javalang.parser.JavaSyntaxError:
            return []

    def print_inheritance_tree(self) -> None:
        """
        Prints the inheritance tree in a user-friendly format.
        """
        if not self.inheritance_graph.nodes:
            print("No inheritance tree to print.")
            return
        
        for node in self.inheritance_graph.nodes:
            parents = list(self.inheritance_graph.predecessors(node))
            file_path = self.class_file_map.get(node, "Unknown file")
            if parents:
                print(f"{node} (in {file_path}) inherits from: {', '.join(parents)}")
            else:
                print(f"{node} (in {file_path}) is a root class/interface")

    def get_class_source_code(self, class_name: str) -> Optional[str]:
        """
        Retrieves the source code of a given class name.
        If multiple classes exist in the same file, returns the entire file content.

        Args:
            class_name: Name of the class to retrieve source code for

        Returns:
            The source code as a string, or None if the class is not found
        """
        if class_name not in self.class_file_map:
            return None
            
        file_path = self.class_file_map[class_name]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                return source_code
        except IOError as e:
            print(f"Error reading file {file_path}: {e}")
            return None
