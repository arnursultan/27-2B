#1
# import sys
# from PyQt6.QtWidgets import QApplication, QLabel, QWidget
#
# app = QApplication(sys.argv)
#
# window = QWidget()
# window.setWindowTitle("Привет, PyQt6!")
# window.setGeometry(100, 100, 300, 200)
#
# label = QLabel("Hello, World!", parent=window)
# label.move(100, 80)
#
# window.show()
#
# sys.exit(app.exec())

#2
# import sys
# from PyQt6.QtWidgets import QApplication, QLabel, QWidget
#
# class MainWindow(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.init_ui()
#
#     def init_ui(self):
#         self.setWindowTitle("Декомпозиция в PyQt6")
#         self.setGeometry(200, 200, 350, 250)
#         label = QLabel("Это окно создано через класс!", self)
#         label.move(50, 100)
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec())