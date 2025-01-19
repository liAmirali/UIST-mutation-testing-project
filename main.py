import tkinter as tk

from src.app import App
from src.gui import MutationTesterGUI

import logging

if __name__ == "__main__":
    root = tk.Tk()

    app = App()
    
    logging.basicConfig(level=logging.DEBUG)

    # app.init(
    #     project_name="amirali4",
    #     source_code_path="dev-junit-runner/src/main/java",
    #     test_code_path="dev-junit-runner/src/test/java",
    # )
    # app.generate_operator_selection("IOD and IOR")
    # results = app.generate_mutations()
    # app.run_mutant_tester(results)

    gui = MutationTesterGUI(root, app)
    root.mainloop()
