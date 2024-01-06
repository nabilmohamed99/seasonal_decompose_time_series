import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QComboBox, QPushButton, QWidget, QProgressBar, QDockWidget
from PyQt5.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.ax = plt.subplots(3, 1, figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
       # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def plot(self, decomposition):
        self.ax[0].clear()
        self.ax[1].clear()
        self.ax[2].clear()

        self.ax[0].plot(decomposition.trend, label='Trend')
        self.ax[1].plot(decomposition.seasonal, label='Seasonal')
        self.ax[2].plot(decomposition.resid, label='Residual')

        self.ax[0].legend()
        self.ax[1].legend()
        self.ax[2].legend()

        self.draw()

class DecompositionThread(QThread):
    decomposition_completed = pyqtSignal(object)

    def __init__(self, data, period):
        super().__init__()
        self.data = data
        self.period = period

    def run(self):
        try:
            decomposition = seasonal_decompose(self.data, period=self.period)
            self.decomposition_completed.emit(decomposition)
        except ValueError as e:
            print(f"Error: {e}")

class MyMainWindow(QMainWindow):
    def __init__(self, df):
        super().__init__()

        self.df = df

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        self.comboBox = QComboBox(self)
        self.comboBox.addItems(df.columns)
        self.main_layout.addWidget(self.comboBox)

        self.plot_button = QPushButton('Plot', self)
        self.plot_button.clicked.connect(self.start_decomposition_thread)
        self.main_layout.addWidget(self.plot_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        self.canvas = MplCanvas(self, width=5, height=8, dpi=100)
        self.main_layout.addWidget(self.canvas)

        # Utilisation de NavigationToolbar2QT
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.addToolBar(self.toolbar)

        self.worker_thread = None

    def start_decomposition_thread(self):
        if self.worker_thread and self.worker_thread.isRunning():
            print("Thread is already running")
            return

        selected_column = self.comboBox.currentText()
        data = self.df[selected_column]

        # Hide the progress bar initially
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Create and start the worker thread
        self.worker_thread = DecompositionThread(data, period=3)  # Adjust the period accordingly
        self.worker_thread.decomposition_completed.connect(self.show_decomposition)
        self.worker_thread.finished.connect(self.hide_progress_bar)
        self.worker_thread.start()

    def show_decomposition(self, decomposition):
        # Hide the progress bar after the decomposition is completed
        self.progress_bar.setVisible(False)
        self.canvas.plot(decomposition)

    def hide_progress_bar(self):
        # Hide the progress bar if the thread finishes (even if it encountered an error)
        self.progress_bar.setVisible(False)

if __name__ == '__main__':
    # Example DataFrame (replace this with your own DataFrame)
    date_rng = pd.date_range(start='2022-01-01', end='2022-01-10', freq='D')
    data = {'colonne_1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'colonne_2': [5, 4, 3, 2, 1, 2, 3, 4, 5, 6]}
    df = pd.DataFrame(data, index=date_rng)

    app = QApplication(sys.argv)
    main_window = MyMainWindow(df)
    main_window.show()
    sys.exit(app.exec_())
