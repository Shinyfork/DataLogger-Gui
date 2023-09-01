import pathlib
import pygubu
import wx
import serial
import com_helper
import tkinter as ttk
import tkinter as tk
from tkinter import filedialog
from datetime import datetime as dt
import time
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas

FRAME_PROJECT_PATH = pathlib.Path(__file__).parent
FRAME_PROJECT_UI = FRAME_PROJECT_PATH / "data_logger_frame.ui"
def set_text(text_ctrl, new_string):
    text_ctrl.delete("1.0", tk.END)
    text_ctrl.insert("1.0", new_string)

class DataLoggerFrameWidget(ttk.Frame):
    def __init__(self, master=None, index=0, **kw):
        super(DataLoggerFrameWidget, self).__init__(master, **kw)
        self.index = index
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(FRAME_PROJECT_PATH)
        builder.add_from_file(FRAME_PROJECT_UI)
        # Main widget
        self.frame = builder.get_object("ID_DATALOGGER_FRAME", master)
        builder.connect_callbacks(self)

        self.port_file_event = f'<<port_and_file_set>>'

        #self.root = tk.Tk()
        #self.root.event_add(self.port_file_event, self.port_file_event)



        self.serial_port = None
        self.baud_rate = None
        self.ser = None
        self.data_list = []
        self.write_data = False
        self.file_selected = False
        self.port_selected = False
        self.csv_file_path = None

        self.combobox = builder.get_object("ID_Combo_1", master)
        self.canvas = builder.get_object("ID_Plot_1", master)
        self.update_interval = 500

        self.data_buffer = ""

        self.plot_fig = plt.figure(figsize=(10, 2))
        self.plot_axes = self.plot_fig.add_subplot(111)
        self.plot_canvas = FigureCanvas(self.plot_fig, master=self.canvas)
        self.axes = []
        # self.ax = self.plot_axes.twinx()
        self.axes.append(self.plot_axes.twinx())
        self.axes.append(self.plot_axes.twinx())
        self.axes.append(self.plot_axes.twinx())
        self.axes.append(self.plot_axes.twinx())

        self.axes[0].set_ylim([0, 10])
        self.axes[1].set_ylim([0, 10])
        self.axes[2].set_ylim([80, 150])
        self.axes[3].set_ylim([0, 10])


        # axes lines same width as plot
        axes_linewidth = 0.5
        self.axes[0].spines['top'].set_linewidth(axes_linewidth)
        self.axes[0].spines['right'].set_linewidth(axes_linewidth)
        self.axes[0].spines['bottom'].set_linewidth(axes_linewidth)
        self.axes[0].spines['left'].set_linewidth(axes_linewidth)
        self.axes[1].spines['top'].set_linewidth(axes_linewidth)
        self.axes[1].spines['right'].set_linewidth(axes_linewidth)
        self.axes[1].spines['bottom'].set_linewidth(axes_linewidth)
        self.axes[1].spines['left'].set_linewidth(axes_linewidth)
        self.axes[2].spines['top'].set_linewidth(axes_linewidth)
        self.axes[2].spines['right'].set_linewidth(axes_linewidth)
        self.axes[2].spines['bottom'].set_linewidth(axes_linewidth)
        self.axes[2].spines['left'].set_linewidth(axes_linewidth)
        self.axes[3].spines['top'].set_linewidth(axes_linewidth)
        self.axes[3].spines['right'].set_linewidth(axes_linewidth)
        self.axes[3].spines['bottom'].set_linewidth(axes_linewidth)
        self.axes[3].spines['left'].set_linewidth(axes_linewidth)

        self.axes[0].set_yticks([0, 2, 4, 6, 8, 10])
        self.axes[1].set_yticks([0, 2, 4, 6, 8, 10])
        self.axes[2].set_yticks([0, 30, 60, 90, 120, 150])
        self.axes[3].set_yticks([0, 20, 40, 60, 80, 100])

        self.axes[0].spines.right.set_position(("axes", 1.12))
        self.axes[0].spines.right.set_color('green')
        self.axes[1].spines.right.set_position(("axes", 1.24))
        self.axes[1].spines.right.set_color('red')
        self.axes[2].spines.right.set_position(("axes", 1.36))
        self.axes[2].spines.right.set_color('orange')
        self.axes[3].spines.right.set_position(("axes", 1.48))
        self.axes[3].spines.right.set_color('blue')

        self.axes[0].set_ylabel("Anzeigewert", color='green')
        self.axes[1].set_ylabel("Druck", color='red')
        self.axes[2].set_ylabel("Rohwert", color="orange")
        self.axes[3].set_ylabel("Temperatur", color='blue')

        self.axes[0].tick_params(axis='y', colors='green')
        self.axes[1].tick_params(axis='y', colors='red')
        self.axes[2].tick_params(axis='y', colors='orange')
        self.axes[3].tick_params(axis='y', colors='blue')

        # grid for plot
        self.axes[0].grid(True, which='major', linestyle='-')
        self.axes[0].grid(True, which='minor', linestyle='--')
        self.axes[0].minorticks_on()
        self.axes[1].minorticks_on()
        self.axes[2].minorticks_on()
        self.axes[3].minorticks_on()

        self.plot_axes.get_yaxis().set_visible(False)
        self.plot_fig.tight_layout()

        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH)
        self.plot_canvas.draw()

        self.label = builder.get_object("ID_DATALOGER_HEADER", self.frame)
        self.label.configure(text=f"Data Logger {index + 1}")

        self.populate_com_ports()
        self.schedule_update()

        # every label in ID_DATALOGER_HEADER gets a new name with a new number









    def on_port_selected(self, event=None):
        self.serial_port = self.combobox.get()
        self.baud_rate = 115200
        self.port_selected = True
        if self.port_selected and self.file_selected:
            self.event_generate(self.port_file_event)





    def set_folder_path(self, folder_path):
        timestamp = dt.now().strftime("%Y%m%d%H%M%S")
        csv_filename = f"data_{timestamp}.csv"
        self.csv_file_path = os.path.join(folder_path, csv_filename)

        df = pd.DataFrame(self.data_list)
        df.to_csv(self.csv_file_path, sep=";", index=False)

        self.file_selected = True
        if self.port_selected and self.file_selected:
            self.event_generate(self.port_file_event)
    def is_ready(self):
        if self.file_selected is True and self.port_selected is True:
            return True
        else:
            return False


    def populate_com_ports(self):
        all_ports = com_helper.iterate_comports()
        self.combobox["values"] = all_ports

    def start_recording(self):
        if self.ser is not None:
            self.ser.close()
        self.ser = serial.Serial(self.serial_port, baudrate=self.baud_rate)
        self.write_data=True


    def stop_recording(self):
        if self.ser is not None:
            self.ser.close()
            self.ser=None
        self.write_data = False

    def plot_canvas(self):
        self.plot_fig = plt.figure(figsize=(10, 5))
        self.plot_axes = self.plot_fig.add_subplot(111)
        self.plot_canvas = FigureCanvas(self.plot_fig, master=self.canvas)
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.plot_canvas.draw()


    def change_serial_port(self, new_port):
        self.baud_rate = 115200
        self.serial_port = new_port

    def schedule_update(self):
        self.after(self.update_interval, self.update_display)

    def update_display(self, event=None):
        try:

            if self.ser is None:
                self.schedule_update()
                return
            bytes_waiting = self.ser.inWaiting()
            if bytes_waiting == 0:
                self.schedule_update()
                return
            bytearr_receive = self.ser.read(bytes_waiting)
            self.data_received = bytearr_receive.decode(encoding="ascii")
            self.data_buffer += self.data_received
            data_lines = self.data_buffer.split("\r", 1)
            if len(data_lines) > 1:
                data_str = data_lines[0]
                data_str = data_str.lstrip("\n")
                self.data_buffer = data_lines[1]
            else:
                self.schedule_update()
                return
            if data_str and self.write_data:
                linefields = data_str.split(",")
                if len(linefields) == 15:
                    timestamp = dt.strptime(linefields[0], "%Y%m%dT%H%M%S")
                    data_values = [val if val != "" else None for val in linefields[1:]]
                    data_dict = {"Timestamp": timestamp}
                    for i, value in enumerate(data_values, start=1):
                        if i in (3, 4, 7, 8, 9, 10, 11, 12, 13, 14):
                            continue
                        data_dict[f"Value{i}"] = float(value)

                    self.data_list.append(data_dict)
                    df = pd.DataFrame(self.data_list)
                    df.to_csv(f'log_{self.serial_port}.csv', sep=";", index=False)
                    display_text = "Time: " + str(df["Timestamp"].iloc[len(df) - 1]) + "\tValue2: " + str(
                        df["Value2"].iloc[len(df) - 1]) + "\t\tValue1: " + str(
                        df["Value1"].iloc[len(df) - 1]) + "\t\tValue5: " + str(
                        df["Value5"].iloc[len(df) - 1]) + "\t\tValue6: " + str(df["Value6"].iloc[len(df) - 1])

                    if len(df) > 0:

                        #for ax in self.axes:
                        #    ax.cla()


                        try:
                            self.plot1.remove()
                            self.plot2.remove()
                            self.plot3.remove()
                            self.plot4.remove()
                        except:
                            pass

                        self.plot1 = self.axes[0].plot(df["Timestamp"], df["Value1"], label="Anzeigewert", color='green', linewidth=0.5)
                        self.plot2 = self.axes[1].plot(df["Timestamp"], df["Value5"], label="Druck", color='red', linewidth=0.5)
                        self.plot3 = self.axes[2].plot(df["Timestamp"], df["Value6"], label="Rohwert", color="orange", linewidth=0.5)
                        self.plot4 = self.axes[3].plot(df["Timestamp"], df["Value2"], label="Temperatur", color='blue', linewidth=0.5)

                        self.plot_fig.tight_layout()
                        self.plot_canvas.draw()

        except Exception as e:
            print(f"An error occurred: {e}")
        self.schedule_update()