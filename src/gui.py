import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import logging

from src.app import App

class MutationTesterGUI:
    def __init__(self, root, app: App):
        self.root = root
        self.root.title("Mutation Testing Tool")
        self.root.geometry("1400x900")
        
        # Store paths and project name
        self.source_folder = None
        self.test_folder = None
        self.project_name = None
        
        # Store app instance
        self.app = None
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.setup_ui()
        
    def setup_ui(self):
        # Create main container with notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Setup pages
        self.setup_project_setup_page()
        self.setup_operator_selection_page()
        self.setup_mutations_page()

    def setup_project_setup_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="Step 1: Project Setup")
        
        # Project name input
        project_frame = ttk.LabelFrame(page, text="Project Name", padding="10")
        project_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.project_name_var = tk.StringVar()
        project_entry = ttk.Entry(project_frame, textvariable=self.project_name_var)
        project_entry.pack(fill=tk.X, expand=True)
        
        # Source folder selection
        source_frame = ttk.LabelFrame(page, text="Source Code Folder", padding="10")
        source_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.source_label = ttk.Label(source_frame, text="No folder selected")
        self.source_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(source_frame, text="Browse", command=self.select_source_folder).pack(side=tk.RIGHT)
        
        # Test folder selection
        test_frame = ttk.LabelFrame(page, text="Test Folder", padding="10")
        test_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.test_label = ttk.Label(test_frame, text="No folder selected")
        self.test_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(test_frame, text="Browse", command=self.select_test_folder).pack(side=tk.RIGHT)
        
        # Initialize Project button
        ttk.Button(page, text="Initialize Project →", command=self.initialize_project).pack(side=tk.BOTTOM, pady=20)
        
    def setup_operator_selection_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="Step 2: Select Operators")
        
        # Testing goal input
        goal_frame = ttk.LabelFrame(page, text="What do you want to test?", padding="10")
        goal_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.goal_text = scrolledtext.ScrolledText(goal_frame, wrap=tk.WORD, height=4)
        self.goal_text.pack(fill=tk.X)
        
        ttk.Button(goal_frame, text="Find Suitable Operators", command=self.find_operators).pack(pady=5)
        
        # Selected operators display
        operators_frame = ttk.LabelFrame(page, text="Recommended Operators", padding="10")
        operators_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.operators_tree = ttk.Treeview(operators_frame, columns=("Operator", "Reason"), show="headings")
        self.operators_tree.heading("Operator", text="Operator")
        self.operators_tree.heading("Reason", text="Reason")
        self.operators_tree.column("Operator", width=100)
        self.operators_tree.column("Reason", width=500)
        self.operators_tree.pack(fill=tk.BOTH, expand=True)
        
        # Navigation buttons
        nav_frame = ttk.Frame(page)
        nav_frame.pack(side=tk.BOTTOM, pady=20)
        ttk.Button(nav_frame, text="← Back", command=lambda: self.notebook.select(0)).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Generate Mutations →", command=self.generate_mutations).pack(side=tk.LEFT, padx=5)
        
    def setup_mutations_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="Step 3: View Mutations")
        
        # Split into left (file list) and right (mutation details) panes
        paned = ttk.PanedWindow(page, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left pane - File list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Source Files").pack(fill=tk.X)
        self.files_tree = ttk.Treeview(left_frame, show="tree")
        self.files_tree.pack(fill=tk.BOTH, expand=True)
        self.files_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
        # Right pane - Mutation details
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        # Mutations list at the top
        mutations_frame = ttk.LabelFrame(right_frame, text="Mutations", padding="5")
        mutations_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mutations_tree = ttk.Treeview(mutations_frame, 
                                         columns=("ID", "Operator", "Line"), 
                                         show="headings",
                                         height=6)
        self.mutations_tree.heading("ID", text="ID")
        self.mutations_tree.heading("Operator", text="Operator")
        self.mutations_tree.heading("Line", text="Line")
        self.mutations_tree.column("ID", width=70)
        self.mutations_tree.column("Operator", width=100)
        self.mutations_tree.column("Line", width=70)
        self.mutations_tree.pack(fill=tk.X)
        self.mutations_tree.bind('<<TreeviewSelect>>', self.on_mutation_select)
        
        # Original code and mutated code side by side
        code_frame = ttk.Frame(right_frame)
        code_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Original code
        original_frame = ttk.LabelFrame(code_frame, text="Original Code", padding="5")
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.original_code = scrolledtext.ScrolledText(original_frame, wrap=tk.NONE)
        self.original_code.pack(fill=tk.BOTH, expand=True)
        
        # Mutated code
        mutated_frame = ttk.LabelFrame(code_frame, text="Mutated Code", padding="5")
        mutated_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.mutated_code = scrolledtext.ScrolledText(mutated_frame, wrap=tk.NONE)
        self.mutated_code.pack(fill=tk.BOTH, expand=True)
        
        # Explanation at the bottom
        explanation_frame = ttk.LabelFrame(right_frame, text="Mutation Explanation", padding="5")
        explanation_frame.pack(fill=tk.X, padx=5, pady=5)
        self.explanation_text = scrolledtext.ScrolledText(explanation_frame, height=4, wrap=tk.WORD)
        self.explanation_text.pack(fill=tk.X)
        
        # Navigation
        ttk.Button(page, text="← Back", command=lambda: self.notebook.select(1)).pack(side=tk.BOTTOM, pady=20)

    def initialize_project(self):
        project_name = self.project_name_var.get().strip()
        if not project_name:
            messagebox.showwarning("Warning", "Please enter a project name")
            return
            
        if not self.source_folder or not self.test_folder:
            messagebox.showwarning("Warning", "Please select both source and test folders")
            return
            
        try:
            self.app = App()
            self.app.init(project_name, self.source_folder, self.test_folder)
            self.notebook.select(1)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize project: {str(e)}")    
    
    def select_source_folder(self):
        folder = filedialog.askdirectory(title="Select Source Code Folder")
        if folder:
            self.source_folder = folder
            self.source_label.config(text=folder)
            
    def select_test_folder(self):
        folder = filedialog.askdirectory(title="Select Test Folder")
        if folder:
            self.test_folder = folder
            self.test_label.config(text=folder)
            
    def proceed_to_operator_selection(self):
        if not self.source_folder or not self.test_folder:
            messagebox.showwarning("Warning", "Please select both source and test folders")
            return
        self.notebook.select(1)
        
    def find_operators(self):
        if not self.app:
            messagebox.showerror("Error", "Project not initialized")
            return
            
        goal = self.goal_text.get('1.0', tk.END).strip()
        if not goal:
            messagebox.showwarning("Warning", "Please describe what you want to test")
            return
            
        try:
            selected_operators = self.app.generate_operator_selection(goal)
            
            # Clear existing items
            for item in self.operators_tree.get_children():
                self.operators_tree.delete(item)
                
            # Add new operators
            for op in selected_operators:
                self.operators_tree.insert("", tk.END, values=(op.operator_name, op.reason))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to find operators: {str(e)}")
            
    def generate_mutations(self):
        if not self.app:
            messagebox.showerror("Error", "Project not initialized")
            return
            
        try:
            mutation_results = self.app.generate_mutations()
            
            # Clear existing items
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
                
            # Process mutation results
            self.mutations_by_file = {}
            for mutation_result in mutation_results:
                for mutation in mutation_result.mutations:
                    if mutation.total_mutations > 0:
                        file_path = self.app.get_file_relpath(mutation.path)
                        self.mutations_by_file[file_path] = {
                            'source': mutation.original_code,
                            'mutations': mutation.mutations
                        }
                        # Add to tree
                        self.files_tree.insert("", tk.END, text=file_path, values=(file_path,))
            
            self.notebook.select(2)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate mutations: {str(e)}")
            
    def on_file_select(self, event):
        selection = self.files_tree.selection()
        if not selection:
            return
            
        file_path = self.files_tree.item(selection[0])["text"]
        file_data = self.mutations_by_file[file_path]
        
        # Clear existing mutations
        for item in self.mutations_tree.get_children():
            self.mutations_tree.delete(item)
            
        # Add mutations for this file
        for mutation in file_data['mutations']:
            self.mutations_tree.insert("", tk.END, 
                                     values=(mutation.id, mutation.operator, 
                                            mutation.location.line_number))
            
        # Show original code
        self.original_code.delete('1.0', tk.END)
        self.original_code.insert('1.0', file_data['source'])
        
        # Clear mutated code and explanation
        self.mutated_code.delete('1.0', tk.END)
        self.explanation_text.delete('1.0', tk.END)
        
    def on_mutation_select(self, event):
        file_selection = self.files_tree.selection()
        mutation_selection = self.mutations_tree.selection()
        
        if not file_selection or not mutation_selection:
            return
            
        file_path = self.files_tree.item(file_selection[0])["text"]
        mutation_id = self.mutations_tree.item(mutation_selection[0])["values"][0]
        
        # Find the selected mutation
        mutation = next(m for m in self.mutations_by_file[file_path]['mutations'] 
                       if m.id == mutation_id)
        
        # Show mutated code
        self.mutated_code.delete('1.0', tk.END)
        self.mutated_code.insert('1.0', mutation.mutated_code)
        
        # Show explanation
        self.explanation_text.delete('1.0', tk.END)
        self.explanation_text.insert('1.0', mutation.explanation)
