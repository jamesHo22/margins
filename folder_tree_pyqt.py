import sys
import os
from PyQt5.QtWidgets import QApplication, QTreeView, QFileSystemModel, QWidget, QVBoxLayout
from PyQt5.QtCore import QDir

class FolderTree(QWidget):
    def __init__(self, root_path):
        super().__init__()
        self.setWindowTitle('Folder Structure Tree (Folders Only)')
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.model = QFileSystemModel()
        self.model.setRootPath(root_path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path))
        self.tree.setColumnHidden(1, True)  # Hide Size
        self.tree.setColumnHidden(2, True)  # Hide Type
        self.tree.setColumnHidden(3, True)  # Hide Date Modified
        layout.addWidget(self.tree)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    root_path = '.'  # You can change this to any path you want
    window = FolderTree(root_path)
    window.show()
    sys.exit(app.exec_())