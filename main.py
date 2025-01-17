import tkinter as tk

from src.operator_selector import OperatorSelector
from src.mutation_assistant import MutationAssistant
from src.vector_store import VectorStore
from src.gui import MutationTesterGUI

if __name__ == "__main__":
    root = tk.Tk()

    vector_store = VectorStore()
    docs = vector_store.load_documents_json("docs.json")
    store = vector_store.create_vector_store(docs)
    
    operator_selector = OperatorSelector(store)
    mutation_assistant = MutationAssistant(store)

    app = MutationTesterGUI(root, operator_selector, mutation_assistant)
    root.mainloop()
