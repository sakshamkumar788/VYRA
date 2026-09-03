import sys
from PySide6.QtWidgets import QApplication
from .window import CatWindow


def main():
    app = QApplication(sys.argv)
    # Ensure clean exit
    app.setQuitOnLastWindowClosed(True)

    window = CatWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
