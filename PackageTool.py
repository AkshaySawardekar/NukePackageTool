import nuke,sys,os,glob,shutil,re
from PySide2.QtWidgets import(QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,QHBoxLayout,QLabel, QLineEdit, QProgressBar,QListWidget,QTableWidget,QHeaderView,QListWidgetItem)
from PySide2.QtCore import Qt, QEventLoop
from PySide2.QtGui import QPixmap,QFont

class PackageTool(QMainWindow):
    def __init__(self):
        super(PackageTool, self).__init__()

        self.initialize_paths()

        self.setWindowTitle("Mill Package Tool")
        self.move(700,300)
        self.resize(500,400)
        self.setWindowFlags(Qt.Window | Qt.Tool)

        self.ext = "_pkg"
        self.setup_ui()

        self.abort_packaging = False

    def initialize_paths(self):
        self.target_classes = ["Read", "ReadGeo2"]
        self.extract_filePath = self.extract_file_paths()
        self.file_paths = self.extract_filePath["paths"]
        self.base_filePath = self.extract_filePath["paths_basename"]

    def extract_file_paths(self):
        nodes = nuke.allNodes()
        paths = []
        paths_basename = []
        for node in nodes:
            if node.Class() in self.target_classes:
                extension = os.path.splitext(node['file'].value())[1][1:]
                file_path = node['file'].value()
                file_basename = os.path.basename(node['file'].value())
                paths_basename.append(file_basename.split('.')[0]+" ["+extension+"]")
                paths.append(file_path)
        return {"paths": paths, "paths_basename": paths_basename}

    def extract_file_dirPath(self):
        nodes = nuke.allNodes()
        script_dirPath = None
        path_found = False
        for node in nodes:
            if node.Class() == "Read":
                script_dirPath = os.path.dirname(node['file'].value())
                path_found = True
                break
        script_dirPath_parts = script_dirPath.split("/")[2:]
        script_dirPath_parts.insert(3, "nuke")
        script_dirPath_parts = script_dirPath_parts[:3+1]
        script_dirPath_parts[0]+= self.ext
        return "/".join(script_dirPath_parts)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()

        self.main_layout.addLayout(self.create_BlackUI_Layout())      
        self.main_layout.addLayout(self.create_project_attribute_layout())
        self.main_layout.addLayout(self.create_proj_job_layout())
        self.main_layout.addLayout(self.create_proj_scene_layout())
        self.main_layout.addLayout(self.create_proj_shot_layout())
        self.main_layout.addLayout(self.create_package_content_with_tooltips())
        self.main_layout.addLayout(self.create_destination_layout())
        self.main_layout.addLayout(self.create_button_layout())

        self.central_widget.setLayout(self.main_layout)

    def create_BlackUI_Layout(self):
        layout = QVBoxLayout()

        black_rectangle = QWidget()
        black_rectangle.setFixedHeight(50)
        black_rectangle.setStyleSheet("background-color:black;")

        layout.addWidget(black_rectangle)

        black_layout = QHBoxLayout(black_rectangle)
        mill_logo = QLabel(black_rectangle)
        pixmap = QPixmap("/usr/people/akshay-sa/Desktop/Mill/Mill_Logo-02.png")
        mill_logo.setPixmap(pixmap)
        mill_logo.setScaledContents(True)       
        mill_logo.setFixedSize(45,30)

        black_layout.addWidget(mill_logo, alignment = Qt.AlignLeft)

        job_name = self.extract_job_name()
        job_name = QLabel(job_name, self)
        font = QFont("Arial", 16)
        font.setBold(True)
        job_name.setFont(font)   
        black_layout.addWidget(job_name, alignment = Qt.AlignCenter)

        version = QLabel('ver 1.0.1', self)
        black_layout.addWidget(version, alignment = Qt.AlignRight)

        return layout

    def create_project_attribute_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel('--Project Attributes--'))

        return layout

    def create_proj_job_layout(self):
        layout = QHBoxLayout()
        job_name = self.extract_job_name()
        layout.addWidget(QLabel('Job:'))
        layout.addSpacing(100)
        layout.addWidget(QLabel(job_name))
        layout.addStretch()

        return layout

    def create_proj_scene_layout(self):
        layout = QHBoxLayout()
        script_path = self.extract_file_dirPath()
        
        layout.addWidget(QLabel('Scene:'))
        layout.addSpacing(82)
        layout.addWidget(QLabel(script_path.split("/")[1]))
        layout.addStretch()

        return layout

    def create_proj_shot_layout(self):
        layout = QHBoxLayout()
        script_path = self.extract_file_dirPath()
        
        layout.addWidget(QLabel('Shot:'))
        layout.addSpacing(91)
        layout.addWidget(QLabel(script_path.split("/")[2]))
        layout.addStretch()

        return layout

    def create_package_content_with_tooltips(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Files to Package:'))

        self.element_list = QListWidget()
        items = self.base_filePath
        tooltips = self.file_paths
        for item_text, tooltip in zip(items, tooltips):
            item = QListWidgetItem(item_text)
            item.setToolTip(tooltip)
            self.element_list.addItem(item)
        layout.addWidget(self.element_list)

        return layout

    def create_destination_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Package Destination:'))

        self.package_path_input = QLineEdit()
        layout.addWidget(self.package_path_input)

        return layout

    def create_button_layout(self):
        layout = QHBoxLayout()
        package_button = QPushButton("[Package]")
        package_button.clicked.connect(self.perform_packaging)
        layout.addWidget(package_button)

        return layout

    def closeEvent(self,event):
        self.abort_packaging = True
        event.accept()

    def extract_job_name(self):
        script_path = self.extract_file_dirPath()
        job_name = script_path.split("/")[0]
        if job_name.endswith("_pkg"):
            job_name = job_name[:-4]
        return job_name

    def perform_packaging(self):
        destination_root = self.package_path_input.text().strip()
        if not destination_root:
            nuke.message("Please specify a destination path.")
            return
        else:
            try:
                self.progress_bar = QProgressBar()
                self.progress_bar.setValue(0)
                self.main_layout.addWidget(self.progress_bar)

                total_files = len(self.file_paths)
                self.progress_bar.setMaximum(total_files)

                for i,file_path in enumerate(self.file_paths):
                    if self.abort_packaging:
                        nuke.message("Packaging aborted by the user.")
                        return
                    self.progress_bar.setValue(i+1)
                    QApplication.processEvents()
                    
                    self.copy_files_to_destination(file_path, destination_root)

                self.copy_script_to_destination(destination_root)
                self.close()
                nuke.message("Packaging Done!")
            except Exception as e:
                nuke.message("Error during packaging: {}".format(str(e)))
                raise
                self.close()
            finally:
                self.close()

    def copy_files_to_destination(self, file_path, destination_root):
        base_path = os.path.dirname(file_path)
        destination_path = os.path.join(destination_root, self.build_destination_subpath(base_path))

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        if re.search(r"%0\d+d", file_path):
            sequence_pattern = re.sub(r"%0\d+d", "*", file_path)
            for file in glob.glob(sequence_pattern):
                shutil.copy2(file, os.path.join(destination_path, os.path.basename(file)))
        else:
            shutil.copy2(file_path, os.path.join(destination_path, os.path.basename(file_path)))

    def build_destination_subpath(self, base_path):
        path_parts = base_path.split("/")[2:]
        path_parts[0]+= self.ext
        return "/".join(path_parts)

    def copy_script_to_destination(self,destination_root):
        script_dirPath = self.extract_file_dirPath()
        nuke.scriptSave("")
        script_name = nuke.root()['name'].value()
        destination_path = os.path.join(destination_root, script_dirPath)

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        shutil.copy2(script_name, destination_path)

        text_file_path = os.path.dirname(destination_path)
        text_file_path +="/packageReport.txt"
        with open(text_file_path, "w") as file:
            file.write(str("\n".join(self.extract_filePath["paths"])))

if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    window = PackageTool()
    window.show()
    app.exec_()
