import pathlib
import pygubu
import wx
import serial
import com_helper
import tkinter as tk
from tkinter import filedialog
from datetime import datetime as dt
import time
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
import data_logger_frame


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "test.ui"


def set_text(text_ctrl, new_string):
    text_ctrl.delete("1.0", tk.END)
    text_ctrl.insert("1.0", new_string)


class TestApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.mainwindow = builder.get_object("MainFrame", master)
        self.button = builder.get_object("ID_Button_Close", master)
        self.Text = builder.get_object("ID_Bottom_Text", master)
        self.start_button = builder.get_object("ID_Button_Start", master)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button = builder.get_object("ID_Button_Stop", master)
        self.stop_button.config(state=tk.DISABLED)
        self.search_button = builder.get_object("ID_Button_Search", master)
        #self.data_logger_frame = data_logger_frame.DataLoggerFrameWidget(master)
        self.scroll_panel = builder.get_object("ID_INNER_SCROLL")
        self.data_logger_frames = []


        for i in range(1):
            dlf = data_logger_frame.DataLoggerFrameWidget(self.scroll_panel, index=i)
            dlf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.NW, pady=3, padx=3, ipady=2, ipadx=2)
            self.data_logger_frames.append(dlf)
            dlf.bind(dlf.port_file_event, self.check_if_ready)






        # TODO: Event binden

        builder.connect_callbacks(self)





    def run(self):
        self.mainwindow.mainloop()


    def on_button_click_close(self, event=None):
        self.mainwindow.destroy()


    def on_search_button(self, event):
        selected_folder_path = filedialog.askdirectory()
        if not selected_folder_path:
            return

        for dlf in self.data_logger_frames:
            dlf.set_folder_path(selected_folder_path)


    def check_if_ready(self, event):
        all_ready = True
        for dlf in self.data_logger_frames:
            if dlf.is_ready() == False:
                all_ready = False
                break

        if all_ready is True:
            # activate start and stop buttons
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)

    def on_start_button(self, event):
        self.data_list = []
        self.write_data = True
        for dlf in self.data_logger_frames:
            dlf.start_recording()

        set_text(self.Text, "Started recording.")

    def on_stop_button(self, event):
        self.write_data = False
        set_text(self.Text, "Data reading stopped.")





if __name__ == "__main__":
    app = TestApp()
    app.run()
