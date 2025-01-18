import tkinter as tk

from src.app import App
from src.gui import MutationTesterGUI

if __name__ == "__main__":
    root = tk.Tk()

    app = App()

    app = MutationTesterGUI(root, app)
    root.mainloop()
