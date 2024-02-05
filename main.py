import atexit
import json
import pathlib
import tkinter as tk
from tkinter import filedialog
import pygubu

import data_logger_frame
from data_logger_frame import DataLoggerFrameWidget

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

        self.Text = builder.get_object("ID_Bottom_Text", master)
        self.start_button = builder.get_object("ID_Button_Start", master)
        self.start_button.config(state=tk.DISABLED)
        self.search_button = builder.get_object("ID_Button_Search", master)
        self.create_button = builder.get_object("ID_Button_Create", master)
        self.create_button.config(state=tk.NORMAL)
        self.create_button.bind("<Button-1>", self.create_widget)
        self.refresh_button = builder.get_object("ID_REFRESH", master)
        self.refresh_button.config(state=tk.NORMAL)
        # button refresh bind on click event to refresh the list of available ports on the combobox with populate_com_ports from dataloggerframe
        self.refresh_button.bind("<Button-1>", lambda event: self.data_logger_frames[0].populate_com_ports(event))



        self.delete_cmd = self.mainwindow.winfo_toplevel().register(self.remove_widget)

        #self.data_logger_frame = data_logger_frame.DataLoggerFrameWidget(master)
        self.scroll_panel = builder.get_object("ID_INNER_SCROLL")
        self.data_logger_frames = []
        self.next_frame_index = 1

        builder.connect_callbacks(self)

        self.load_from_json("data_logger_frame.json")
        atexit.register(self.save_on_exit)

    def save_to_json(self, file_path):
        data_json = []
        for dlf in self.data_logger_frames:
            data_json.append(dlf.to_json())

        main_json = {
            "dataloggers": data_json
        }


        with open(file_path, 'w') as json_file:
            json.dump(main_json, json_file)

    def load_data_from_json(self, file_path):
        try:
            with open(file_path, 'r') as json_file:
                loaded_data = json.load(json_file)
            return loaded_data
        except FileNotFoundError:
            return None

    def load_from_json(self, file_path):
        loaded_data = self.load_data_from_json(file_path)
        if loaded_data:
            for data in loaded_data.get("dataloggers", []):
                self.widget_from_json(data)
        self.check_if_ready(event=None)
    def save_on_exit(self):

        self.save_to_json("data_logger_frame.json")

    def widget_from_json(self, json_data):
        dlf = data_logger_frame.DataLoggerFrameWidget(self.scroll_panel, index=self.next_frame_index)
        dlf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.NW, pady=3, padx=3, ipady=2, ipadx=2)
        self.data_logger_frames.append(dlf)


        if "serial_port" in json_data:
            dlf.change_serial_port(json_data["serial_port"])
            try:
                dlf.combobox.set(json_data["serial_port"])
            except:
                pass
        if "baud_rate" in json_data:
            dlf.baud_rate = json_data["baud_rate"]
        if "folder_path" in json_data:
            dlf.set_folder_path(json_data["folder_path"])
        if "file_selected" in json_data and json_data["file_selected"]:
            dlf.file_selected = True
        if "port_selected" in json_data and json_data["port_selected"]:
            dlf.port_selected = True



        dlf.bind(dlf.port_file_event, self.check_if_ready)
        dlf.bind("<<RemoveMe>>", lambda event: self.remove_widget(event, dlf))
        self.next_frame_index += 1


    def create_widget(self, index_to_remove):

        i = len(self.data_logger_frames)
        dlf = data_logger_frame.DataLoggerFrameWidget(self.scroll_panel, index=i)
        dlf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.NW, pady=3, padx=3, ipady=2, ipadx=2)
        self.data_logger_frames.append(dlf)
        dlf.bind(dlf.port_file_event, self.check_if_ready)

        self.next_frame_index += 1

        dlf.bind("<<RemoveMe>>", lambda event: self.remove_widget(event, dlf))

    def remove_widget(self, event=None, datalogger=None):
        for dlf in self.data_logger_frames:
            if dlf == datalogger:
                self.data_logger_frames.remove(dlf)


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


    def on_start_button(self, event):
        self.data_list = []
        self.write_data = True
        for dlf in self.data_logger_frames:
            dlf.start_recording()

        set_text(self.Text, "Started recording.")







if __name__ == "__main__":
    app = TestApp()
    app.run()
