#!/usr/bin/env python3
"""
Interactive folder tree diagram visualization using PyQt5.
Supports both QWidget (original) and QGraphicsView (optimized) implementations.
"""

import os
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QScrollArea, QMenu, QAction,
                             QInputDialog, QMessageBox, QGraphicsView, QGraphicsScene,
                             QGraphicsTextItem, QGraphicsLineItem, QGraphicsItem)
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
import datetime

class TreeNode:
    """Represents a node in the tree structure"""
    def __init__(self, name, path, x=0, y=0):
        self.name = name
        self.path = path
        self.x = x
        self.y = y
        self.children = []
        self.parent = None
        self.width = 120
        self.height = 40
        self.focused = False
        self.selected = False

class OptimizedTreeDiagram(QGraphicsView):
    """Optimized tree diagram using QGraphicsView for better performance with large datasets"""
    
    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.root_node = None
        self.focused_node = None
        self.selected_node = None
        self.debug_mode = False
        
        # Setup the graphics scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Enable smooth scrolling
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # Store graphics items for easy access
        self.node_items = {}  # path -> QGraphicsTextItem
        self.connection_items = []  # list of QGraphicsLineItem
        
        # Build the tree
        self.build_tree()
        self.recalculate_all_positions()
        
        # Set focus policy for keyboard navigation
        self.setFocusPolicy(Qt.StrongFocus)
        
    def build_tree(self):
        """Build the tree structure from the file system"""
        self.root_node = TreeNode(os.path.basename(self.root_path), self.root_path)
        self.build_tree_recursive(self.root_path, self.root_node, 0)
        
    def build_tree_recursive(self, path, parent_node, level):
        """Recursively build the tree structure"""
        try:
            items = os.listdir(path)
            for item in sorted(items):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    child_node = TreeNode(item, item_path)
                    child_node.parent = parent_node
                    parent_node.children.append(child_node)
                    self.build_tree_recursive(item_path, child_node, level + 1)
        except PermissionError:
            pass  # Skip directories we can't access
            
    def recalculate_all_positions(self):
        """Recalculate positions for all nodes"""
        if self.root_node:
            self.calculate_positions(self.root_node, 0, 0)
            self.resolve_overlaps()
            self.update_graphics_items()
            
    def calculate_positions(self, node, x, y):
        """Calculate positions for a node and its children"""
        node.x = x
        node.y = y
        
        if node.children:
            # Calculate child positions
            child_x = x - (len(node.children) - 1) * 150 // 2
            for child in node.children:
                self.calculate_positions(child, child_x, y + 100)
                child_x += 150
                
    def resolve_overlaps(self):
        """Resolve overlapping nodes"""
        all_nodes = self.get_all_nodes(self.root_node)
        self.resolve_level_overlaps(all_nodes)
        self.resolve_vertical_overlaps(all_nodes)
        
    def get_all_nodes(self, node):
        """Get all nodes in the tree"""
        nodes = [node]
        for child in node.children:
            nodes.extend(self.get_all_nodes(child))
        return nodes
        
    def resolve_level_overlaps(self, all_nodes):
        """Resolve overlaps within the same level"""
        levels = {}
        for node in all_nodes:
            level = self.get_node_level(node)
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
            
        for level_nodes in levels.values():
            if len(level_nodes) > 1:
                level_nodes.sort(key=lambda n: n.x)
                for i in range(1, len(level_nodes)):
                    prev_node = level_nodes[i-1]
                    curr_node = level_nodes[i]
                    if curr_node.x - prev_node.x < 150:
                        curr_node.x = prev_node.x + 150
                        
    def get_node_level(self, node):
        """Get the level of a node in the tree"""
        level = 0
        current = node
        while current.parent:
            level += 1
            current = current.parent
        return level
        
    def resolve_vertical_overlaps(self, all_nodes):
        """Resolve vertical overlaps between nodes"""
        for i, node1 in enumerate(all_nodes):
            for node2 in all_nodes[i+1:]:
                if self.nodes_overlap(node1, node2):
                    self.separate_overlapping_nodes(node1, node2)
                    
    def nodes_overlap(self, node1, node2):
        """Check if two nodes overlap"""
        return (abs(node1.x - node2.x) < 150 and 
                abs(node1.y - node2.y) < 50)
                
    def separate_overlapping_nodes(self, node1, node2):
        """Separate two overlapping nodes"""
        if node1.y == node2.y:
            # Same level, adjust X
            if node1.x < node2.x:
                node2.x = node1.x + 150
            else:
                node1.x = node2.x + 150
        else:
            # Different levels, adjust Y
            if node1.y < node2.y:
                node2.y = node1.y + 100
            else:
                node1.y = node2.y + 100
                
    def update_graphics_items(self):
        """Update all graphics items in the scene"""
        # Clear existing items
        self.scene.clear()
        self.node_items.clear()
        self.connection_items.clear()
        
        # Add all nodes and connections
        if self.root_node:
            self.add_node_to_scene(self.root_node)
            
        # Fit the view to show all content
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def add_node_to_scene(self, node):
        """Add a node and its connections to the scene"""
        # Create text item for the node
        text_item = QGraphicsTextItem(node.name)
        text_item.setPos(node.x - node.width//2, node.y - node.height//2)
        text_item.setDefaultTextColor(Qt.black)
        
        # Set background color based on node state
        if node.focused:
            text_item.setDefaultTextColor(Qt.white)
            text_item.setBackground(QBrush(QColor(255, 165, 0)))  # Orange for focused
        elif node.selected:
            text_item.setDefaultTextColor(Qt.white)
            text_item.setBackground(QBrush(QColor(100, 150, 255)))  # Blue for selected
            
        self.scene.addItem(text_item)
        self.node_items[node.path] = text_item
        
        # Add connections to children
        for child in node.children:
            self.add_connection_to_scene(node, child)
            self.add_node_to_scene(child)
            
    def add_connection_to_scene(self, parent, child):
        """Add a connection line between parent and child"""
        line = QGraphicsLineItem(parent.x, parent.y + parent.height//2,
                                child.x, child.y - child.height//2)
        line.setPen(QPen(Qt.black, 2))
        self.scene.addItem(line)
        self.connection_items.append(line)
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        super().mousePressEvent(event)
        
        # Get the item under the mouse
        item = self.itemAt(event.pos())
        if item and isinstance(item, QGraphicsTextItem):
            # Find the corresponding node
            node = self.find_node_by_item(item)
            if node:
                if event.button() == Qt.LeftButton:
                    self.show_directory_contents(node)
                elif event.button() == Qt.RightButton:
                    self.show_context_menu(node, event.globalPos())
                    
    def find_node_by_item(self, item):
        """Find the TreeNode corresponding to a graphics item"""
        for path, graphics_item in self.node_items.items():
            if graphics_item == item:
                return self.find_node_by_path(self.root_node, path)
        return None
        
    def find_node_by_path(self, node, path):
        """Find a node by its path"""
        if node.path == path:
            return node
        for child in node.children:
            found = self.find_node_by_path(child, path)
            if found:
                return found
        return None
        
    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        if not self.focused_node:
            self.focused_node = self.root_node
            
        if event.key() == Qt.Key_Up:
            self.navigate_up()
        elif event.key() == Qt.Key_Down:
            self.navigate_down()
        elif event.key() == Qt.Key_Left:
            self.navigate_left()
        elif event.key() == Qt.Key_Right:
            self.navigate_right()
        elif event.key() == Qt.Key_N and event.modifiers() == Qt.ControlModifier:
            self.create_new_folder_at_focused()
        else:
            super().keyPressEvent(event)
            
    def navigate_up(self):
        """Navigate to the node above the focused node"""
        if not self.focused_node:
            return
            
        # Find all nodes at the same level
        level = self.get_node_level(self.focused_node)
        same_level_nodes = [n for n in self.get_all_nodes(self.root_node) 
                           if self.get_node_level(n) == level]
        
        # Find the node above
        same_level_nodes.sort(key=lambda n: n.y)
        current_index = same_level_nodes.index(self.focused_node)
        if current_index > 0:
            self.set_focused_node(same_level_nodes[current_index - 1])
            
    def navigate_down(self):
        """Navigate to the node below the focused node"""
        if not self.focused_node:
            return
            
        # Find all nodes at the same level
        level = self.get_node_level(self.focused_node)
        same_level_nodes = [n for n in self.get_all_nodes(self.root_node) 
                           if self.get_node_level(n) == level]
        
        # Find the node below
        same_level_nodes.sort(key=lambda n: n.y)
        current_index = same_level_nodes.index(self.focused_node)
        if current_index < len(same_level_nodes) - 1:
            self.set_focused_node(same_level_nodes[current_index + 1])
            
    def navigate_left(self):
        """Navigate to the left sibling"""
        if not self.focused_node or not self.focused_node.parent:
            return
            
        siblings = self.focused_node.parent.children
        current_index = siblings.index(self.focused_node)
        if current_index > 0:
            self.set_focused_node(siblings[current_index - 1])
            
    def navigate_right(self):
        """Navigate to the right sibling"""
        if not self.focused_node or not self.focused_node.parent:
            return
            
        siblings = self.focused_node.parent.children
        current_index = siblings.index(self.focused_node)
        if current_index < len(siblings) - 1:
            self.set_focused_node(siblings[current_index + 1])
            
    def set_focused_node(self, node):
        """Set the focused node and update display"""
        if self.focused_node:
            self.focused_node.focused = False
        self.focused_node = node
        if node:
            node.focused = True
            self.ensure_focused_node_visible()
        self.update_graphics_items()
        
    def ensure_focused_node_visible(self):
        """Ensure the focused node is visible in the viewport"""
        if self.focused_node:
            rect = QRect(self.focused_node.x - 100, self.focused_node.y - 50, 200, 100)
            self.ensureVisible(rect)
            
    def create_new_folder_at_focused(self):
        """Create a new folder under the focused node"""
        if not self.focused_node:
            return
            
        folder_name, ok = QInputDialog.getText(self, "Create Folder", 
                                             f"Enter folder name to create inside '{self.focused_node.name}':")
        if ok and folder_name.strip():
            try:
                new_folder_path = os.path.join(self.focused_node.path, folder_name.strip())
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                    self.build_tree()
                    self.recalculate_all_positions()
                else:
                    QMessageBox.warning(self, "Error", 
                                      f"Folder '{folder_name}' already exists!")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to create folder: {str(e)}")
                                   
    def show_directory_contents(self, node):
        """Open the native folder viewer for the clicked directory"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(['open', node.path])
            elif system == "Windows":
                subprocess.run(['explorer', node.path])
            elif system == "Linux":
                file_managers = ['xdg-open', 'nautilus', 'dolphin', 'thunar']
                for fm in file_managers:
                    try:
                        subprocess.run([fm, node.path])
                        break
                    except FileNotFoundError:
                        continue
                else:
                    try:
                        subprocess.run(['xdg-open', node.path])
                    except FileNotFoundError:
                        QMessageBox.warning(self, "Error", 
                                          "No file manager found.")
                        return
            else:
                QMessageBox.warning(self, "Error", 
                                  f"Unsupported operating system: {system}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open folder: {str(e)}")
                               
    def show_context_menu(self, node, pos):
        """Show context menu for a node"""
        menu = QMenu(self)
        
        # Create subfolder action
        create_action = QAction("Create Subfolder", self)
        create_action.triggered.connect(lambda: self.create_subfolder(node))
        menu.addAction(create_action)
        
        menu.addSeparator()
        
        # Rename action (only for non-root nodes)
        if node != self.root_node:
            rename_action = QAction("Rename Folder", self)
            rename_action.triggered.connect(lambda: self.rename_folder(node))
            menu.addAction(rename_action)
        
        # Delete action (only for non-root nodes)
        if node != self.root_node:
            delete_action = QAction("Delete Folder", self)
            delete_action.triggered.connect(lambda: self.delete_folder(node))
            menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Properties action
        properties_action = QAction("Properties", self)
        properties_action.triggered.connect(lambda: self.show_properties(node))
        menu.addAction(properties_action)

        # Create Template action (only for non-root nodes)
        if node != self.root_node:
            create_template_action = QAction("Create Template", self)
            create_template_action.triggered.connect(lambda: self.create_template_from_node(node))
            menu.addAction(create_template_action)

        # Apply Template action (only for non-root nodes)
        if node != self.root_node:
            apply_template_action = QAction("Apply Template", self)
            apply_template_action.triggered.connect(lambda: self.apply_template_to_node(node))
            menu.addAction(apply_template_action)
        
        menu.exec_(pos)
        
    def create_subfolder(self, node):
        """Create a subfolder under the specified node"""
        folder_name, ok = QInputDialog.getText(self, "Create Subfolder", 
                                             f"Enter folder name to create inside '{node.name}':")
        if ok and folder_name.strip():
            try:
                new_folder_path = os.path.join(node.path, folder_name.strip())
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                    self.build_tree()
                    self.recalculate_all_positions()
                else:
                    QMessageBox.warning(self, "Error", 
                                      f"Folder '{folder_name}' already exists in '{node.name}'!")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to create folder: {str(e)}")
                                   
    def rename_folder(self, node):
        """Rename a folder"""
        new_name, ok = QInputDialog.getText(self, "Rename Folder", 
                                          f"Enter new name for '{node.name}':",
                                          text=node.name)
        if ok and new_name.strip() and new_name.strip() != node.name:
            try:
                parent_path = os.path.dirname(node.path)
                new_path = os.path.join(parent_path, new_name.strip())
                if not os.path.exists(new_path):
                    os.rename(node.path, new_path)
                    self.build_tree()
                    self.recalculate_all_positions()
                else:
                    QMessageBox.warning(self, "Error", 
                                      f"Folder '{new_name}' already exists!")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to rename folder: {str(e)}")
                                   
    def delete_folder(self, node):
        """Delete a folder"""
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete '{node.name}' and all its contents?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                import shutil
                shutil.rmtree(node.path)
                self.build_tree()
                self.recalculate_all_positions()
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to delete folder: {str(e)}")
                                   
    def show_properties(self, node):
        """Show properties of a folder"""
        try:
            import stat
            stats = os.stat(node.path)
            size = 0
            file_count = 0
            dir_count = 0
            
            # Count files and directories
            for root, dirs, files in os.walk(node.path):
                dir_count += len(dirs)
                for file in files:
                    try:
                        size += os.path.getsize(os.path.join(root, file))
                        file_count += 1
                    except:
                        pass
            
            info = f"Name: {node.name}\n"
            info += f"Path: {node.path}\n"
            info += f"Size: {size:,} bytes\n"
            info += f"Files: {file_count}\n"
            info += f"Directories: {dir_count}\n"
            info += f"Created: {stats.st_ctime}\n"
            info += f"Modified: {stats.st_mtime}"
            
            QMessageBox.information(self, "Properties", info)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get properties: {str(e)}")
            
    def create_template_from_node(self, node):
        """Create a template from a folder structure"""
        try:
            # Create .templates directory if it doesn't exist
            templates_dir = os.path.join(os.getcwd(), ".templates")
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            
            # Get template name
            template_name, ok = QInputDialog.getText(self, "Create Template", 
                                                  "Enter template name:")
            if not ok or not template_name.strip():
                return
                
            template_filename = os.path.join(templates_dir, f"{template_name}.txt")
            
            # Get folder structure
            structure = self.get_folder_structure(node)
            
            # Write template file
            with open(template_filename, 'w') as f:
                f.write(f"# Template: {template_name}\n")
                f.write(f"# Created from: {node.name}\n")
                f.write(f"# Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(structure)
                
            QMessageBox.information(self, "Success", 
                                  f"Template '{template_name}' created successfully!")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to create template: {str(e)}")
                               
    def get_folder_structure(self, node, prefix=""):
        """Get the folder structure as a string"""
        result = prefix + node.name + "/\n"
        for child in node.children:
            result += self.get_folder_structure(child, prefix + "  ")
        return result
        
    def apply_template_to_node(self, node):
        """Apply a template to a folder"""
        try:
            # Get available templates
            templates_dir = os.path.join(os.getcwd(), ".templates")
            if not os.path.exists(templates_dir):
                QMessageBox.warning(self, "No Templates", 
                                  "No templates found. Create a template first.")
                return
                
            template_files = [f for f in os.listdir(templates_dir) if f.endswith('.txt')]
            if not template_files:
                QMessageBox.warning(self, "No Templates", 
                                  "No templates found. Create a template first.")
                return
                
            # Let user select template
            template_name, ok = QInputDialog.getItem(self, "Apply Template", 
                                                  "Select template to apply:",
                                                  template_files, 0, False)
            if not ok:
                return
                
            # Read template content
            template_path = os.path.join(templates_dir, template_name)
            with open(template_path, 'r') as f:
                template_content = f.read()
                
            # Apply template
            self.create_structure_from_template(node, template_content)
            
            # Refresh the tree
            self.build_tree()
            self.recalculate_all_positions()
            
            QMessageBox.information(self, "Success", 
                                  f"Template '{template_name}' applied successfully!")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to apply template: {str(e)}")
                               
    def create_structure_from_template(self, parent_node, template_content):
        """Create folder structure from template content under the selected folder"""
        lines = template_content.split('\n')
        
        # Find the template root name (first non-comment line)
        template_root_name = None
        for line in lines:
            check_line = line.strip()
            if check_line and not check_line.startswith('#'):
                template_root_name = check_line.rstrip('/').strip()
                break
        
        if not template_root_name:
            return
        
        # Create the template root folder under the selected folder
        template_root_path = os.path.join(parent_node.path, template_root_name)
        if not os.path.exists(template_root_path):
            os.makedirs(template_root_path)
        
        # Now process all lines to create the structure under the template root
        level_stack = [template_root_path]
        
        for line in lines:
            if not line.strip() or line.strip().startswith('#'):
                continue
            # Count leading spaces BEFORE stripping
            indent = len(line) - len(line.lstrip(' '))
            level = indent // 2
            folder_name = line.strip().rstrip('/')
            if level == 0:
                continue  # already created root
            adjusted_level = level - 1
            while len(level_stack) <= adjusted_level:
                level_stack.append(level_stack[-1])
            if adjusted_level == 0:
                current_parent = template_root_path
            else:
                current_parent = level_stack[adjusted_level - 1]
            new_folder_path = os.path.join(current_parent, folder_name)
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            if adjusted_level < len(level_stack):
                level_stack[adjusted_level] = new_folder_path
            else:
                level_stack.append(new_folder_path)

class TreeDiagram(QWidget):
    def __init__(self, root_path):
        super().__init__()
        self.setWindowTitle('Folder Structure Tree Diagram')
        self.root_path = root_path
        self.root_node = None
        self.node_spacing_x = 40  # Reduced from 60
        self.node_spacing_y = 80  # Reduced from 60
        self.selected_node = None
        self.focused_node = None  # Track keyboard-focused node
        self.debug_mode = False  # Add debug mode flag
        # Create a large canvas for infinite scrolling
        self.canvas_width = 4000  # Increased from 2000
        self.canvas_height = 4000  # Increased from 2000
        self.canvas_center_x = self.canvas_width // 2
        self.canvas_center_y = self.canvas_height // 2
        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)
        self.build_tree()
        # Set focus to root node initially
        self.focused_node = self.root_node

    def build_tree(self):
        self.root_node = TreeNode(os.path.basename(os.path.abspath(self.root_path)), os.path.abspath(self.root_path))
        self.build_tree_recursive(self.root_path, self.root_node, 0)
        self.recalculate_all_positions()
        self.selected_node = None
        # Set the widget size to the large canvas
        self.setMinimumSize(self.canvas_width, self.canvas_height)
        self.update()

    def recalculate_all_positions(self):
        """Recalculate positions for the entire tree to prevent overlaps"""
        # Start positioning from the center of the canvas
        self.calculate_positions(self.root_node, self.canvas_center_x, self.canvas_center_y)
        self.resolve_overlaps()
        self.update()

    def resolve_overlaps(self):
        """Resolve any remaining overlaps by adjusting positions"""
        all_nodes = self.get_all_nodes(self.root_node)
        
        # Check for horizontal overlaps between nodes at the same level
        for level in range(self.get_max_level(self.root_node) + 1):
            level_nodes = [node for node in all_nodes if node.level == level]
            self.resolve_level_overlaps(level_nodes)
        
        # Check for vertical overlaps between different levels
        self.resolve_vertical_overlaps(all_nodes)
        
        # Final check for any remaining overlaps
        self.final_overlap_check(all_nodes)

    def final_overlap_check(self, all_nodes):
        """Final check to resolve any remaining overlaps"""
        for i, node1 in enumerate(all_nodes):
            for node2 in all_nodes[i+1:]:
                if self.nodes_overlap(node1, node2):
                    # Move node2 to avoid overlap
                    self.separate_overlapping_nodes(node1, node2)

    def separate_overlapping_nodes(self, node1, node2):
        """Separate two overlapping nodes by moving one of them"""
        # Calculate the overlap
        overlap_x = min(node1.x + node1.width//2, node2.x + node2.width//2) - max(node1.x - node1.width//2, node2.x - node2.width//2)
        overlap_y = min(node1.y + node1.height//2, node2.y + node2.height//2) - max(node1.y - node1.height//2, node2.y - node2.height//2)
        
        if overlap_x > 0 and overlap_y > 0:
            # Move node2 to avoid overlap
            separation_x = overlap_x + 10  # 10px buffer
            separation_y = overlap_y + 10  # 10px buffer
            
            # Move node2 to the right and down
            node2.x += separation_x
            node2.y += separation_y

    def get_all_nodes(self, node):
        """Get all nodes in the tree"""
        nodes = [node]
        for child in node.children:
            nodes.extend(self.get_all_nodes(child))
        return nodes

    def get_max_level(self, node):
        """Get the maximum level in the tree"""
        max_level = node.level
        for child in node.children:
            max_level = max(max_level, self.get_max_level(child))
        return max_level

    def resolve_level_overlaps(self, level_nodes):
        """Resolve overlaps between nodes at the same level"""
        if len(level_nodes) < 2:
            return
        
        # Sort nodes by x position
        level_nodes.sort(key=lambda n: n.x)
        
        for i in range(len(level_nodes) - 1):
            current = level_nodes[i]
            next_node = level_nodes[i + 1]
            
            # Check if nodes overlap horizontally
            current_right = current.x + current.width // 2
            next_left = next_node.x - next_node.width // 2
            
            if current_right >= next_left:
                # Calculate required spacing
                required_spacing = (current.width + next_node.width) // 2 + 20  # 20px buffer
                current_spacing = next_node.x - current.x
                
                if current_spacing < required_spacing:
                    # Move the next node and all subsequent nodes
                    adjustment = required_spacing - current_spacing
                    for j in range(i + 1, len(level_nodes)):
                        level_nodes[j].x += adjustment

    def resolve_vertical_overlaps(self, all_nodes):
        """Resolve vertical overlaps between nodes at different levels"""
        # Group nodes by level
        levels = {}
        for node in all_nodes:
            if node.level not in levels:
                levels[node.level] = []
            levels[node.level].append(node)
        
        # Check for overlaps between adjacent levels
        for level in sorted(levels.keys()):
            if level == 0:
                continue
            
            current_level_nodes = levels[level]
            parent_level_nodes = levels.get(level - 1, [])
            
            for current_node in current_level_nodes:
                # Find parent node
                parent_node = self.find_parent_node(self.root_node, current_node)
                if parent_node:
                    # Check if current node overlaps with any node at parent level
                    for parent_level_node in parent_level_nodes:
                        if self.nodes_overlap(current_node, parent_level_node):
                            # Move current node down
                            overlap_amount = self.get_vertical_overlap(current_node, parent_level_node)
                            current_node.y += overlap_amount + 10  # 10px buffer

    def find_parent_node(self, root, target_node):
        """Find the parent of a given node"""
        for child in root.children:
            if child == target_node:
                return root
            parent = self.find_parent_node(child, target_node)
            if parent:
                return parent
        return None

    def nodes_overlap(self, node1, node2):
        """Check if two nodes overlap"""
        # Check horizontal overlap
        node1_left = node1.x - node1.width // 2
        node1_right = node1.x + node1.width // 2
        node2_left = node2.x - node2.width // 2
        node2_right = node2.x + node2.width // 2
        
        horizontal_overlap = not (node1_right < node2_left or node1_left > node2_right)
        
        # Check vertical overlap
        node1_top = node1.y - node1.height // 2
        node1_bottom = node1.y + node1.height // 2
        node2_top = node2.y - node2.height // 2
        node2_bottom = node2.y + node2.height // 2
        
        vertical_overlap = not (node1_bottom < node2_top or node1_top > node2_bottom)
        
        return horizontal_overlap and vertical_overlap

    def get_vertical_overlap(self, node1, node2):
        """Calculate the amount of vertical overlap between two nodes"""
        node1_top = node1.y - node1.height // 2
        node1_bottom = node1.y + node1.height // 2
        node2_top = node2.y - node2.height // 2
        node2_bottom = node2.y + node2.height // 2
        
        if node1_bottom <= node2_top or node1_top >= node2_bottom:
            return 0
        
        # Calculate overlap amount
        overlap_top = max(node1_top, node2_top)
        overlap_bottom = min(node1_bottom, node2_bottom)
        return overlap_bottom - overlap_top

    def ensure_minimum_spacing_recursive(self, node):
        """Recursively ensure minimum spacing between all nodes"""
        if len(node.children) > 1:
            self.ensure_minimum_spacing(node)
        for child in node.children:
            self.ensure_minimum_spacing_recursive(child)

    def ensure_minimum_spacing(self, parent_node):
        """Ensure minimum spacing between sibling nodes to prevent overlap"""
        if len(parent_node.children) < 2:
            return
            
        # Calculate minimum spacing based on actual node widths
        min_spacing = max(self.node_spacing_x, 
                         (parent_node.children[0].width + parent_node.children[0].width) // 2 + 20)
        
        for i in range(len(parent_node.children) - 1):
            current_child = parent_node.children[i]
            next_child = parent_node.children[i + 1]
            actual_spacing = next_child.x - current_child.x
            
            # Calculate required spacing based on actual node dimensions
            required_spacing = (current_child.width + next_child.width) // 2 + 20  # 20px buffer
            
            if actual_spacing < required_spacing:
                # Calculate how much we need to move the next child
                needed_adjustment = required_spacing - actual_spacing
                
                # Move all children after this point
                for j in range(i + 1, len(parent_node.children)):
                    parent_node.children[j].x += needed_adjustment

    def build_tree_recursive(self, path, parent_node, level):
        try:
            for entry in sorted(os.listdir(path)):
                # Skip hidden files/folders that start with .
                if entry.startswith('.'):
                    continue
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):  # ← This line ensures only folders are added
                    # Skip venv folder
                    if entry == 'venv':
                        continue
                    child_node = TreeNode(entry, full_path)
                    child_node.level = level + 1
                    parent_node.children.append(child_node)
                    self.build_tree_recursive(full_path, child_node, level + 1)
            # Always sort children alphabetically by name for stable layout
            parent_node.children.sort(key=lambda n: n.name.lower())
        except PermissionError:
            pass

    def calculate_positions(self, node, x, y):
        spacing = 40
        if not node.children:
            node.x = int(x)
            node.y = int(y)
            return x - node.width // 2, x + node.width // 2

        # Recursively layout children, left to right
        child_spans = []
        for i, child in enumerate(node.children):
            if i == 0:
                child_x = x
            else:
                prev_right = child_spans[-1][1]
                child_x = prev_right + spacing + child.width // 2
            left, right = self.calculate_positions(child, child_x, y + self.node_spacing_y)
            child_spans.append((left, right))

        # Center this parent above its children
        leftmost = child_spans[0][0]
        rightmost = child_spans[-1][1]
        node.x = int((leftmost + rightmost) // 2)
        node.y = int(y)
        return leftmost, rightmost

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont("Arial", 9)
        painter.setFont(font)
        self.draw_node(painter, self.root_node)

    def draw_node(self, painter, node):
        # Draw node at its absolute position on the large canvas
        rect = QRect(int(node.x - node.width//2), int(node.y - node.height//2), node.width, node.height)
        
        # Check for overlaps in debug mode
        is_overlapping = False
        if hasattr(self, 'debug_mode') and self.debug_mode:
            all_nodes = self.get_all_nodes(self.root_node)
            for other_node in all_nodes:
                if other_node != node and self.nodes_overlap(node, other_node):
                    is_overlapping = True
                    break
        
        # Determine node color based on state
        if is_overlapping:
            painter.setBrush(QBrush(QColor(255, 0, 0)))  # Red for overlapping nodes
        elif node == self.focused_node:
            painter.setBrush(QBrush(QColor(255, 165, 0)))  # Orange for focused node
        elif node == self.selected_node:
            painter.setBrush(QBrush(QColor(255, 165, 0)))  # Orange for selected
        else:
            painter.setBrush(QBrush(QColor(70, 130, 180)))  # Steel blue
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(QColor(255, 255, 255))
        text_rect = QRect(int(node.x - node.width//2), int(node.y - node.height//2), node.width, node.height)
        painter.drawText(text_rect, Qt.AlignCenter, node.name)
        
        # Draw orthogonal connections to children
        for child in node.children:
            self.draw_orthogonal_connection(painter, node, child)
            self.draw_node(painter, child)

    def draw_orthogonal_connection(self, painter, parent, child):
        """Draw an orthogonal (right-angled) connection between parent and child nodes"""
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        
        # Calculate connection points
        parent_bottom = QPoint(int(parent.x), int(parent.y + parent.height//2))
        child_top = QPoint(int(child.x), int(child.y - child.height//2))
        
        # Determine the best routing to avoid overlaps
        route = self.calculate_orthogonal_route(parent_bottom, child_top, parent, child)
        
        # Draw the orthogonal path
        if len(route) >= 2:
            for i in range(len(route) - 1):
                painter.drawLine(route[i], route[i + 1])

    def calculate_orthogonal_route(self, start_point, end_point, parent_node, child_node):
        """Calculate an orthogonal route between two points that avoids overlaps"""
        # Get all nodes to check for overlaps
        all_nodes = self.get_all_nodes(self.root_node)
        
        # Try different routing strategies in order of preference
        routes = [
            self.route_simple_vertical_first(start_point, end_point),
            self.route_simple_horizontal_first(start_point, end_point),
            self.route_around_obstacles(start_point, end_point, all_nodes, parent_node, child_node)
        ]
        
        # Choose the first non-overlapping route
        for route in routes:
            if route and len(route) >= 2:
                # Check if route overlaps with any nodes
                overlaps = self.route_overlaps_with_nodes(route, all_nodes, parent_node, child_node)
                if not overlaps:
                    return route
        
        # If no non-overlapping route found, use the simplest one
        return self.route_simple_vertical_first(start_point, end_point)

    def route_simple_vertical_first(self, start, end):
        """Simple vertical-first routing: down, then horizontal, then down"""
        # Go down from parent
        down_point = QPoint(int(start.x()), int(start.y() + 20))
        # Go horizontal to child's x position
        horizontal_point = QPoint(int(end.x()), int(start.y() + 20))
        # Go down to child
        return [start, down_point, horizontal_point, end]

    def route_simple_horizontal_first(self, start, end):
        """Simple horizontal-first routing: horizontal, then down"""
        # Go horizontal to child's x position
        horizontal_point = QPoint(int(end.x()), int(start.y()))
        # Go down to child
        return [start, horizontal_point, end]

    def route_around_obstacles(self, start, end, all_nodes, parent_node, child_node):
        """Route around obstacles by finding clear paths"""
        # Find a clear vertical path first
        clear_x = self.find_clear_vertical_path(start.x(), end.x(), all_nodes, parent_node, child_node)
        if clear_x is not None:
            return [start, QPoint(int(clear_x), int(start.y())), QPoint(int(clear_x), int(end.y())), end]
        
        # If no clear vertical path, try horizontal routing
        clear_y = self.find_clear_horizontal_path(start.y(), end.y(), all_nodes, parent_node, child_node)
        if clear_y is not None:
            return [start, QPoint(int(start.x()), int(clear_y)), QPoint(int(end.x()), int(clear_y)), end]
        
        # Fallback to simple routing
        return self.route_simple_vertical_first(start, end)

    def find_clear_vertical_path(self, start_x, end_x, all_nodes, parent_node, child_node):
        """Find a clear vertical path between two x-coordinates"""
        # Try the midpoint first
        mid_x = (start_x + end_x) // 2
        if self.is_clear_vertical_path(mid_x, all_nodes, parent_node, child_node):
            return mid_x
        
        # Try positions around the midpoint
        for offset in range(50, 200, 25):
            for direction in [-1, 1]:
                test_x = mid_x + (offset * direction)
                if self.is_clear_vertical_path(test_x, all_nodes, parent_node, child_node):
                    return test_x
        
        return None

    def find_clear_horizontal_path(self, start_y, end_y, all_nodes, parent_node, child_node):
        """Find a clear horizontal path between two y-coordinates"""
        # Try the midpoint first
        mid_y = (start_y + end_y) // 2
        if self.is_clear_horizontal_path(mid_y, all_nodes, parent_node, child_node):
            return mid_y
        
        # Try positions around the midpoint
        for offset in range(30, 150, 20):
            for direction in [-1, 1]:
                test_y = mid_y + (offset * direction)
                if self.is_clear_horizontal_path(test_y, all_nodes, parent_node, child_node):
                    return test_y
        
        return None

    def is_clear_vertical_path(self, x, all_nodes, parent_node, child_node):
        """Check if a vertical line at x-coordinate is clear of nodes"""
        for node in all_nodes:
            if node == parent_node or node == child_node:
                continue
            
            node_left = node.x - node.width // 2
            node_right = node.x + node.width // 2
            
            # Check if the vertical line overlaps with this node
            if node_left <= x <= node_right:
                return False
        
        return True

    def is_clear_horizontal_path(self, y, all_nodes, parent_node, child_node):
        """Check if a horizontal line at y-coordinate is clear of nodes"""
        for node in all_nodes:
            if node == parent_node or node == child_node:
                continue
            
            node_top = node.y - node.height // 2
            node_bottom = node.y + node.height // 2
            
            # Check if the horizontal line overlaps with this node
            if node_top <= y <= node_bottom:
                return False
        
        return True

    def route_overlaps_with_nodes(self, route, all_nodes, parent_node, child_node):
        """Check if a route overlaps with any nodes"""
        for i in range(len(route) - 1):
            line_start = route[i]
            line_end = route[i + 1]
            
            for node in all_nodes:
                if node == parent_node or node == child_node:
                    continue
                
                if self.line_intersects_node(line_start, line_end, node):
                    return True
        
        return False

    def line_intersects_node(self, line_start, line_end, node):
        """Check if a line segment intersects with a node"""
        # Get node bounds
        node_left = node.x - node.width // 2
        node_right = node.x + node.width // 2
        node_top = node.y - node.height // 2
        node_bottom = node.y + node.height // 2
        
        # Check if line intersects with node rectangle
        return self.line_intersects_rect(line_start, line_end, 
                                       node_left, node_top, node_right, node_bottom)

    def line_intersects_rect(self, line_start, line_end, rect_left, rect_top, rect_right, rect_bottom):
        """Check if a line segment intersects with a rectangle"""
        # Check if either endpoint is inside the rectangle
        if (rect_left <= line_start.x() <= rect_right and 
            rect_top <= line_start.y() <= rect_bottom):
            return True
        
        if (rect_left <= line_end.x() <= rect_right and 
            rect_top <= line_end.y() <= rect_bottom):
            return True
        
        # Check if line intersects with any of the rectangle's edges
        edges = [
            ((int(rect_left), int(rect_top)), (int(rect_right), int(rect_top))),      # Top edge
            ((int(rect_right), int(rect_top)), (int(rect_right), int(rect_bottom))),  # Right edge
            ((int(rect_right), int(rect_bottom)), (int(rect_left), int(rect_bottom))), # Bottom edge
            ((int(rect_left), int(rect_bottom)), (int(rect_left), int(rect_top)))     # Left edge
        ]
        
        for edge_start, edge_end in edges:
            if self.lines_intersect(line_start, line_end, 
                                  QPoint(edge_start[0], edge_start[1]), 
                                  QPoint(edge_end[0], edge_end[1])):
                return True
        
        return False

    def lines_intersect(self, line1_start, line1_end, line2_start, line2_end):
        """Check if two line segments intersect"""
        def ccw(A, B, C):
            return (C.y() - A.y()) * (B.x() - A.x()) > (B.y() - A.y()) * (C.x() - A.x())
        
        A, B = line1_start, line1_end
        C, D = line2_start, line2_end
        
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    def calculate_route_score(self, route):
        """Calculate a score for a route (lower is better)"""
        if not route or len(route) < 2:
            return float('inf')
        
        # Calculate total length
        total_length = 0
        for i in range(len(route) - 1):
            dx = route[i+1].x() - route[i].x()
            dy = route[i+1].y() - route[i].y()
            total_length += (dx*dx + dy*dy)**0.5
        
        # Penalize number of turns
        num_turns = len(route) - 2
        
        return total_length + (num_turns * 10)  # 10 points per turn

    def mousePressEvent(self, event):
        # Ensure this widget gets focus when clicked
        self.setFocus()
        
        clicked_node = self.find_node_at(self.root_node, event.pos())
        if clicked_node:
            self.selected_node = clicked_node
            self.focused_node = clicked_node  # Update focused node on click
            self.update()
            if event.button() == Qt.LeftButton:
                self.show_directory_contents(clicked_node)
            elif event.button() == Qt.RightButton:
                self.show_context_menu(clicked_node, event.globalPos())
        else:
            self.selected_node = None
            self.update()

    def keyPressEvent(self, event):
        """Handle keyboard navigation and shortcuts"""
        if not self.focused_node:
            return
            
        if event.key() == Qt.Key_Up:
            self.navigate_up()
        elif event.key() == Qt.Key_Down:
            self.navigate_down()
        elif event.key() == Qt.Key_Left:
            self.navigate_left()
        elif event.key() == Qt.Key_Right:
            self.navigate_right()
        elif event.key() == Qt.Key_N and event.modifiers() == Qt.ControlModifier:
            self.create_new_folder_at_focused()
        else:
            super().keyPressEvent(event)

    def ensure_focused_node_visible(self):
        """Ensure the focused node is visible in the scroll area"""
        if not self.focused_node:
            return
            
        # Get the parent scroll area
        parent = self.parent()
        while parent and not hasattr(parent, 'scroll_area'):
            parent = parent.parent()
            
        if parent and hasattr(parent, 'scroll_area'):
            scroll_area = parent.scroll_area
            # Calculate the position of the focused node
            node_rect = QRect(int(self.focused_node.x - self.focused_node.width//2), 
                             int(self.focused_node.y - self.focused_node.height//2),
                             self.focused_node.width, self.focused_node.height)
            
            # Ensure the node is visible in the scroll area
            scroll_area.ensureVisible(node_rect.center().x(), node_rect.center().y(), 
                                    node_rect.width() + 50, node_rect.height() + 50)

    def navigate_up(self):
        """Navigate to the node above the current focused node based on spatial position"""
        if not self.focused_node:
            return
            
        all_nodes = self.get_all_nodes(self.root_node)
        best_candidate = None
        min_distance = float('inf')
        
        for node in all_nodes:
            if node == self.focused_node:
                continue
                
            # Only consider nodes that are above the current node (smaller y coordinate)
            if node.y < self.focused_node.y:
                # Calculate horizontal distance
                horizontal_distance = abs(node.x - self.focused_node.x)
                vertical_distance = self.focused_node.y - node.y
                
                # Prefer nodes that are more directly above (smaller horizontal distance)
                # but also consider vertical distance to avoid jumping too far
                distance_score = horizontal_distance + (vertical_distance * 0.5)
                
                if distance_score < min_distance:
                    min_distance = distance_score
                    best_candidate = node
        
        if best_candidate:
            self.focused_node = best_candidate
            self.selected_node = self.focused_node
            self.ensure_focused_node_visible()
            self.update()

    def navigate_down(self):
        """Navigate to the node below the current focused node based on spatial position"""
        if not self.focused_node:
            return
            
        all_nodes = self.get_all_nodes(self.root_node)
        best_candidate = None
        min_distance = float('inf')
        
        for node in all_nodes:
            if node == self.focused_node:
                continue
                
            # Only consider nodes that are below the current node (larger y coordinate)
            if node.y > self.focused_node.y:
                # Calculate horizontal distance
                horizontal_distance = abs(node.x - self.focused_node.x)
                vertical_distance = node.y - self.focused_node.y
                
                # Prefer nodes that are more directly below (smaller horizontal distance)
                # but also consider vertical distance to avoid jumping too far
                distance_score = horizontal_distance + (vertical_distance * 0.5)
                
                if distance_score < min_distance:
                    min_distance = distance_score
                    best_candidate = node
        
        if best_candidate:
            self.focused_node = best_candidate
            self.selected_node = self.focused_node
            self.ensure_focused_node_visible()
            self.update()

    def navigate_left(self):
        """Navigate to the node to the left of the current focused node based on spatial position"""
        if not self.focused_node:
            return
            
        all_nodes = self.get_all_nodes(self.root_node)
        best_candidate = None
        min_distance = float('inf')
        
        for node in all_nodes:
            if node == self.focused_node:
                continue
                
            # Only consider nodes that are to the left of the current node (smaller x coordinate)
            if node.x < self.focused_node.x:
                # Calculate vertical distance
                vertical_distance = abs(node.y - self.focused_node.y)
                horizontal_distance = self.focused_node.x - node.x
                
                # Prefer nodes that are more directly to the left (smaller vertical distance)
                # but also consider horizontal distance to avoid jumping too far
                distance_score = vertical_distance + (horizontal_distance * 0.5)
                
                if distance_score < min_distance:
                    min_distance = distance_score
                    best_candidate = node
        
        if best_candidate:
            self.focused_node = best_candidate
            self.selected_node = self.focused_node
            self.ensure_focused_node_visible()
            self.update()

    def navigate_right(self):
        """Navigate to the node to the right of the current focused node based on spatial position"""
        if not self.focused_node:
            return
            
        all_nodes = self.get_all_nodes(self.root_node)
        best_candidate = None
        min_distance = float('inf')
        
        for node in all_nodes:
            if node == self.focused_node:
                continue
                
            # Only consider nodes that are to the right of the current node (larger x coordinate)
            if node.x > self.focused_node.x:
                # Calculate vertical distance
                vertical_distance = abs(node.y - self.focused_node.y)
                horizontal_distance = node.x - self.focused_node.x
                
                # Prefer nodes that are more directly to the right (smaller vertical distance)
                # but also consider horizontal distance to avoid jumping too far
                distance_score = vertical_distance + (horizontal_distance * 0.5)
                
                if distance_score < min_distance:
                    min_distance = distance_score
                    best_candidate = node
        
        if best_candidate:
            self.focused_node = best_candidate
            self.selected_node = self.focused_node
            self.ensure_focused_node_visible()
            self.update()

    def create_new_folder_at_focused(self):
        """Create a new folder under the currently focused node"""
        if not self.focused_node:
            return
            
        folder_name, ok = QInputDialog.getText(self, "Create New Folder", 
                                             f"Enter folder name to create inside '{self.focused_node.name}':")
        if ok and folder_name.strip():
            try:
                new_folder_path = os.path.join(self.focused_node.path, folder_name.strip())
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                    self.build_tree()
                    self.recalculate_all_positions()
                    # Keep the same focused node after rebuild
                    self.focused_node = self.find_node_by_path(self.root_node, self.focused_node.path)
                    self.update()
                else:
                    QMessageBox.warning(self, "Error", 
                                      f"Folder '{folder_name}' already exists in '{self.focused_node.name}'!")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to create folder: {str(e)}")

    def find_node_by_path(self, node, path):
        """Find a node by its path"""
        if node.path == path:
            return node
        for child in node.children:
            found = self.find_node_by_path(child, path)
            if found:
                return found
        return None

    def create_template_from_node(self, node):
        """Create a template from the folder structure starting at the given node"""
        try:
            template_name, ok = QInputDialog.getText(self, "Create Template", 
                                                   f"Enter template name for '{node.name}':")
            if ok and template_name.strip():
                # Get the folder structure as a tree
                structure = self.get_folder_structure(node)
                
                # Create templates directory if it doesn't exist
                templates_dir = os.path.join(self.root_path, ".templates")
                if not os.path.exists(templates_dir):
                    os.makedirs(templates_dir)
                
                # Save template to file
                template_file = os.path.join(templates_dir, f"{template_name.strip()}.txt")
                with open(template_file, 'w') as f:
                    f.write(f"# Template: {template_name.strip()}\n")
                    f.write(f"# Created from: {node.name}\n")
                    f.write(f"# Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(structure)
                
                QMessageBox.information(self, "Template Created", 
                                      f"Template '{template_name.strip()}' has been saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to create template: {str(e)}")

    def get_folder_structure(self, node, prefix=""):
        """Recursively get the folder structure as a text representation"""
        structure = f"{prefix}{node.name}/\n"
        for child in node.children:
            structure += self.get_folder_structure(child, prefix + "  ")
        return structure

    def apply_template_to_node(self, node):
        """Apply a template to the given node"""
        try:
            # Get available templates
            templates_dir = os.path.join(self.root_path, ".templates")
            if not os.path.exists(templates_dir):
                QMessageBox.information(self, "No Templates", 
                                      "No templates found. Create a template first by right-clicking a folder and selecting 'Create Template'.")
                return
            
            template_files = [f for f in os.listdir(templates_dir) if f.endswith('.txt')]
            if not template_files:
                QMessageBox.information(self, "No Templates", 
                                      "No templates found. Create a template first by right-clicking a folder and selecting 'Create Template'.")
                return
            
            # Let user select a template
            template_names = [os.path.splitext(f)[0] for f in template_files]
            template_name, ok = QInputDialog.getItem(self, "Select Template", 
                                                   "Choose a template to apply:", template_names, 0, False)
            if ok and template_name:
                # Read the template
                template_file = os.path.join(templates_dir, f"{template_name}.txt")
                with open(template_file, 'r') as f:
                    template_content = f.read()
                
                # Parse and create the structure
                self.create_structure_from_template(node, template_content)
                
                # Rebuild the tree
                self.build_tree()
                self.recalculate_all_positions()
                self.update()
                
                QMessageBox.information(self, "Template Applied", 
                                      f"Template '{template_name}' has been applied successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to apply template: {str(e)}")

    def create_structure_from_template(self, parent_node, template_content):
        """Create folder structure from template content under the selected folder"""
        lines = template_content.split('\n')
        
        # Find the template root name (first non-comment line)
        template_root_name = None
        for line in lines:
            check_line = line.strip()
            if check_line and not check_line.startswith('#'):
                template_root_name = check_line.rstrip('/').strip()
                break
        
        if not template_root_name:
            return
        
        # Create the template root folder under the selected folder
        template_root_path = os.path.join(parent_node.path, template_root_name)
        if not os.path.exists(template_root_path):
            os.makedirs(template_root_path)
        
        # Now process all lines to create the structure under the template root
        level_stack = [template_root_path]
        
        for line in lines:
            if not line.strip() or line.strip().startswith('#'):
                continue
            # Count leading spaces BEFORE stripping
            indent = len(line) - len(line.lstrip(' '))
            level = indent // 2
            folder_name = line.strip().rstrip('/')
            if level == 0:
                continue  # already created root
            adjusted_level = level - 1
            while len(level_stack) <= adjusted_level:
                level_stack.append(level_stack[-1])
            if adjusted_level == 0:
                current_parent = template_root_path
            else:
                current_parent = level_stack[adjusted_level - 1]
            new_folder_path = os.path.join(current_parent, folder_name)
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            if adjusted_level < len(level_stack):
                level_stack[adjusted_level] = new_folder_path
            else:
                level_stack.append(new_folder_path)

    def show_context_menu(self, node, pos):
        menu = QMenu(self)
        
        # Create subfolder action
        create_action = QAction("Create Subfolder", self)
        create_action.triggered.connect(lambda: self.create_subfolder(node))
        menu.addAction(create_action)
        
        menu.addSeparator()
        
        # Rename action (only for non-root nodes)
        if node != self.root_node:
            rename_action = QAction("Rename Folder", self)
            rename_action.triggered.connect(lambda: self.rename_folder(node))
            menu.addAction(rename_action)
        
        # Delete action (only for non-root nodes)
        if node != self.root_node:
            delete_action = QAction("Delete Folder", self)
            delete_action.triggered.connect(lambda: self.delete_folder(node))
            menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Properties action
        properties_action = QAction("Properties", self)
        properties_action.triggered.connect(lambda: self.show_properties(node))
        menu.addAction(properties_action)

        # Create Template action (only for non-root nodes)
        if node != self.root_node:
            create_template_action = QAction("Create Template", self)
            create_template_action.triggered.connect(lambda: self.create_template_from_node(node))
            menu.addAction(create_template_action)

        # Apply Template action (only for non-root nodes)
        if node != self.root_node:
            apply_template_action = QAction("Apply Template", self)
            apply_template_action.triggered.connect(lambda: self.apply_template_to_node(node))
            menu.addAction(apply_template_action)
        
        menu.exec_(pos)

    def show_directory_contents(self, node):
        """Open the native folder viewer (Finder on Mac) for the clicked directory"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Use 'open' command to open Finder
                subprocess.run(['open', node.path])
            elif system == "Windows":
                # Use 'explorer' command to open Windows Explorer
                subprocess.run(['explorer', node.path])
            elif system == "Linux":
                # Try common file managers on Linux
                file_managers = ['xdg-open', 'nautilus', 'dolphin', 'thunar']
                for fm in file_managers:
                    try:
                        subprocess.run([fm, node.path])
                        break
                    except FileNotFoundError:
                        continue
                else:
                    # Fallback to xdg-open if available
                    try:
                        subprocess.run(['xdg-open', node.path])
                    except FileNotFoundError:
                        QMessageBox.warning(self, "Error", 
                                          "No file manager found. Please install a file manager like Nautilus, Dolphin, or Thunar.")
                        return
            else:
                QMessageBox.warning(self, "Error", 
                                  f"Unsupported operating system: {system}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open folder: {str(e)}")

    def find_node_at(self, node, pos):
        rect = QRect(int(node.x - node.width//2), int(node.y - node.height//2), node.width, node.height)
        if rect.contains(pos):
            return node
        for child in node.children:
            found = self.find_node_at(child, pos)
            if found:
                return found
        return None

    def create_subfolder(self, node):
        folder_name, ok = QInputDialog.getText(self, "Create Subfolder", 
                                             f"Enter folder name to create inside '{node.name}':")
        if ok and folder_name.strip():
            try:
                new_folder_path = os.path.join(node.path, folder_name.strip())
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                    self.build_tree()
                    self.recalculate_all_positions()
                    self.update()
                else:
                    QMessageBox.warning(self, "Error", 
                                      f"Folder '{folder_name}' already exists in '{node.name}'!")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to create folder: {str(e)}")

    def rename_folder(self, node):
        new_name, ok = QInputDialog.getText(self, "Rename Folder", 
                                          f"Enter new name for '{node.name}':",
                                          text=node.name)
        if ok and new_name.strip() and new_name.strip() != node.name:
            try:
                parent_path = os.path.dirname(node.path)
                new_path = os.path.join(parent_path, new_name.strip())
                if not os.path.exists(new_path):
                    os.rename(node.path, new_path)
                    self.build_tree()
                    self.recalculate_all_positions()
                    self.update()
                else:
                    QMessageBox.warning(self, "Error", 
                                      f"Folder '{new_name}' already exists!")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to rename folder: {str(e)}")

    def delete_folder(self, node):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete '{node.name}' and all its contents?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                import shutil
                shutil.rmtree(node.path)
                self.build_tree()
                self.recalculate_all_positions()
                self.update()
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to delete folder: {str(e)}")

    def show_properties(self, node):
        try:
            import stat
            stats = os.stat(node.path)
            size = 0
            file_count = 0
            dir_count = 0
            
            # Count files and directories
            for root, dirs, files in os.walk(node.path):
                dir_count += len(dirs)
                for file in files:
                    try:
                        size += os.path.getsize(os.path.join(root, file))
                        file_count += 1
                    except:
                        pass
            
            # Format size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024**2:
                size_str = f"{size/1024:.1f} KB"
            elif size < 1024**3:
                size_str = f"{size/1024**2:.1f} MB"
            else:
                size_str = f"{size/1024**3:.1f} GB"
            
            info = f"""Folder Properties:
            
Name: {node.name}
Path: {node.path}
Size: {size_str}
Files: {file_count}
Subdirectories: {dir_count}
Created: {stats.st_ctime}
Modified: {stats.st_mtime}"""
            
            QMessageBox.information(self, f"Properties - {node.name}", info)
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to get folder properties: {str(e)}")

class ScrollableTreeDiagram(QWidget):
    def __init__(self, root_path):
        super().__init__()
        self.setWindowTitle('Folder Structure Tree Diagram')
        self.setGeometry(100, 100, 1200, 800)
        self.root_path = root_path
        layout = QVBoxLayout()
        self.setLayout(layout)
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        self.add_folder_button = QPushButton("Create New Folder (at root)")
        self.add_folder_button.clicked.connect(self.create_folder)
        button_layout.addWidget(self.add_folder_button)
        
        # Add debug toggle button
        self.debug_button = QPushButton("Toggle Debug Mode")
        self.debug_button.clicked.connect(self.toggle_debug_mode)
        button_layout.addWidget(self.debug_button)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        self.tree_diagram = TreeDiagram(root_path)
        scroll_area.setWidget(self.tree_diagram)
        self.scroll_area = scroll_area
        # Center the scroll area on the root node
        self.center_on_root()
        
    def create_folder(self):
        folder_name, ok = QInputDialog.getText(self, "Create Folder", 
                                             "Enter folder name:")
        if ok and folder_name.strip():
            try:
                new_folder_path = os.path.join(self.root_path, folder_name.strip())
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                    self.tree_diagram.build_tree()
                    self.tree_diagram.recalculate_all_positions()
                    self.tree_diagram.update()
                    self.center_on_root()
                else:
                    QMessageBox.warning(self, "Error", 
                                      f"Folder '{folder_name}' already exists!")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to create folder: {str(e)}")
    
    def toggle_debug_mode(self):
        self.tree_diagram.debug_mode = not self.tree_diagram.debug_mode
        self.tree_diagram.update()
        self.debug_button.setText("Toggle Debug Mode" if self.tree_diagram.debug_mode else "Enable Debug Mode")

    def center_on_root(self):
        # Center the scroll area on the root node
        td = self.tree_diagram
        center_x = int(td.root_node.x)
        center_y = int(td.root_node.y)
        hbar = self.scroll_area.horizontalScrollBar()
        vbar = self.scroll_area.verticalScrollBar()
        hbar.setValue(center_x - self.scroll_area.viewport().width() // 2)
        vbar.setValue(center_y - self.scroll_area.viewport().height() // 2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    root_path = '.'  # Change this to any path you want
    window = ScrollableTreeDiagram(root_path)
    window.show()
    sys.exit(app.exec_()) 