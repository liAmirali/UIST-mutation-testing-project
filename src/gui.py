import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import logging

from src.app import App

class MutationTesterGUI:
    def __init__(self, root, app: App):
        # Set up logging configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Initializing MutationTesterGUI")

        self.root = root
        self.root.title("Mutation Testing Tool")
        self.root.geometry("1400x900")
        
        # Store paths and project name
        self.source_folder = None
        self.test_folder = None
        self.project_name = None
        
        # Store app instance
        self.app = None
        
        # Initialize components
        self.setup_ui()
        self.logger.info("GUI initialization completed")
        
    def setup_ui(self):
        self.logger.debug("Setting up UI components")
        try:
            # Create main container with notebook
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Setup pages
            self.setup_project_setup_page()
            self.setup_operator_selection_page()
            self.setup_mutations_page()
            
            self.logger.debug("UI setup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during UI setup: {str(e)}", exc_info=True)
            raise

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
        self.logger.info(f"Attempting to initialize project: {project_name}")
        
        if not project_name:
            self.logger.warning("Project initialization failed: No project name provided")
            messagebox.showwarning("Warning", "Please enter a project name")
            return
            
        if not self.source_folder or not self.test_folder:
            self.logger.warning("Project initialization failed: Missing source or test folder")
            messagebox.showwarning("Warning", "Please select both source and test folders")
            return
            
        try:
            self.logger.debug(f"Initializing App with: project_name={project_name}, "
                            f"source_folder={self.source_folder}, test_folder={self.test_folder}")
            self.app = App()
            self.app.init(project_name, self.source_folder, self.test_folder)
            self.logger.info("Project initialized successfully")
            self.notebook.select(1)
        except ValueError as e:
            self.logger.error(f"Project initialization failed with ValueError: {str(e)}")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.logger.error(f"Project initialization failed with unexpected error", exc_info=True)
            messagebox.showerror("Error", f"Failed to initialize project: {str(e)}")    
    
    def select_source_folder(self):
        self.logger.debug("Opening source folder selection dialog")
        folder = filedialog.askdirectory(title="Select Source Code Folder")
        if folder:
            self.logger.info(f"Source folder selected: {folder}")
            self.source_folder = folder
            self.source_label.config(text=folder)
        else:
            self.logger.debug("Source folder selection cancelled")

    def select_test_folder(self):
        self.logger.debug("Opening test folder selection dialog")
        folder = filedialog.askdirectory(title="Select Test Folder")
        if folder:
            self.logger.info(f"Test folder selected: {folder}")
            self.test_folder = folder
            self.test_label.config(text=folder)
        else:
            self.logger.debug("Test folder selection cancelled")
            
    def proceed_to_operator_selection(self):
        if not self.source_folder or not self.test_folder:
            messagebox.showwarning("Warning", "Please select both source and test folders")
            return
        self.notebook.select(1)
        
    def find_operators(self):
        if not self.app:
            self.logger.error("Operator selection failed: Project not initialized")
            messagebox.showerror("Error", "Project not initialized")
            return
            
        goal = self.goal_text.get('1.0', tk.END).strip()
        self.logger.info(f"Finding operators for goal: {goal}")
        
        if not goal:
            self.logger.warning("Operator selection failed: No goal provided")
            messagebox.showwarning("Warning", "Please describe what you want to test")
            return
            
        try:
            self.logger.debug("Calling generate_operator_selection")
            selected_operators = self.app.generate_operator_selection(goal)
            
            # Clear existing items
            self.operators_tree.delete(*self.operators_tree.get_children())
            
            # Add new operators
            for op in selected_operators:
                self.logger.debug(f"Adding operator: {op.operator_name}")
                self.operators_tree.insert("", tk.END, values=(op.operator_name, op.reason))
                
            self.logger.info(f"Successfully found {len(selected_operators)} operators")
                
        except Exception as e:
            self.logger.error("Failed to find operators", exc_info=True)
            messagebox.showerror("Error", f"Failed to find operators: {str(e)}")
            
    def generate_mutations(self):
        if not self.app:
            self.logger.error("Mutation generation failed: Project not initialized")
            messagebox.showerror("Error", "Project not initialized")
            return
            
        try:
            self.logger.info("Starting mutation generation")
            mutation_results = self.app.generate_mutations()
            
            # Clear existing items
            self.files_tree.delete(*self.files_tree.get_children())
            
            # Process mutation results
            self.mutations_by_file = {}
            total_mutations = 0
            
            self.logger.debug("Processing mutation results")
            for mutation_result in mutation_results:
                for mutation in mutation_result.mutations:
                    if mutation.total_mutations > 0:
                        file_path = self.app.get_file_relpath(mutation.path)
                        self.logger.debug(f"Processing mutations for file: {file_path}")
                        self.mutations_by_file[file_path] = {
                            'source': mutation.original_code,
                            'mutations': mutation.mutations
                        }
                        self.files_tree.insert("", tk.END, text=file_path, values=(file_path,))
                        total_mutations += mutation.total_mutations
            
            self.logger.info(f"Generated {total_mutations} mutations across {len(self.mutations_by_file)} files")
            self.notebook.select(2)
            
        except Exception as e:
            self.logger.error("Failed to generate mutations", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate mutations: {str(e)}")
            
    def on_file_select(self, event):
        selection = self.files_tree.selection()
        if not selection:
            self.logger.debug("No file selected")
            return
            
        file_path = self.files_tree.item(selection[0])["text"]
        self.logger.debug(f"File selected: {file_path}")
        
        try:
            file_data = self.mutations_by_file[file_path]
            
            # Clear existing mutations
            self.mutations_tree.delete(*self.mutations_tree.get_children())
            
            # Add mutations for this file
            for mutation in file_data['mutations']:
                self.logger.debug(f"Adding mutation: ID={mutation.id}, Operator={mutation.operator}")
                self.mutations_tree.insert("", tk.END, 
                                         values=(mutation.id, mutation.operator, 
                                                mutation.location.line_number))
            
            # Show original code
            self.original_code.delete('1.0', tk.END)
            self.original_code.insert('1.0', file_data['source'])
            
            # Clear mutated code and explanation
            self.mutated_code.delete('1.0', tk.END)
            self.explanation_text.delete('1.0', tk.END)
            
        except Exception as e:
            self.logger.error(f"Error processing file selection", exc_info=True)
            messagebox.showerror("Error", f"Error displaying file contents: {str(e)}")

    def on_mutation_select(self, event):
        file_selection = self.files_tree.selection()
        mutation_selection = self.mutations_tree.selection()
        
        if not file_selection or not mutation_selection:
            self.logger.debug("No complete selection for mutation display")
            return
            
        try:
            file_path = self.files_tree.item(file_selection[0])["text"]
            mutation_id = self.mutations_tree.item(mutation_selection[0])["values"][0]
            
            self.logger.debug(f"Mutation selected: file={file_path}, mutation_id={mutation_id}")
            
            # Find the selected mutation
            mutation = next(m for m in self.mutations_by_file[file_path]['mutations'] 
                          if m.id == mutation_id)
            
            # Show mutated code
            self.mutated_code.delete('1.0', tk.END)
            self.mutated_code.insert('1.0', mutation.mutated_code)
            
            # Show explanation
            self.explanation_text.delete('1.0', tk.END)
            self.explanation_text.insert('1.0', mutation.explanation)
            
            self.logger.debug(f"Successfully displayed mutation details")
            
        except StopIteration:
            self.logger.error(f"Mutation {mutation_id} not found in file {file_path}")
            messagebox.showerror("Error", "Selected mutation not found")
        except Exception as e:
            self.logger.error("Error displaying mutation details", exc_info=True)
            messagebox.showerror("Error", f"Error displaying mutation: {str(e)}")
