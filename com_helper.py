import serial

from serial import *
from serial.tools.list_ports_windows import *
from _winapi import *

def iterate_comports():
    all_ports = []
    """Return a generator that yields descriptions for serial ports"""
    GUIDs = (GUID * 8)()  # so far only seen one used, so hope 8 are enough...
    guids_size = DWORD()
    if not SetupDiClassGuidsFromName(
            "Ports",
            GUIDs,
            ctypes.sizeof(GUIDs),
            ctypes.byref(guids_size)):
        raise ctypes.WinError()

    # repeat for all possible GUIDs
    for index in range(guids_size.value):
        bInterfaceNumber = None
        g_hdi = SetupDiGetClassDevs(
            ctypes.byref(GUIDs[index]),
            None,
            NULL,
            DIGCF_PRESENT | 4)  # @@@ added DIGCF_ALLCLASSES (i.e. 4)

        devinfo = SP_DEVINFO_DATA()
        devinfo.cbSize = ctypes.sizeof(devinfo)
        index = 0
        while SetupDiEnumDeviceInfo(g_hdi, index, ctypes.byref(devinfo)):
            index += 1

            # get the real com port name
            hkey = SetupDiOpenDevRegKey(
                g_hdi,
                ctypes.byref(devinfo),
                DICS_FLAG_GLOBAL,
                0,
                DIREG_DEV,  # DIREG_DRV for SW info
                KEY_READ)
            port_name_buffer = ctypes.create_unicode_buffer(250)
            port_name_length = ULONG(ctypes.sizeof(port_name_buffer))
            RegQueryValueEx(
                hkey,
                "PortName",
                None,
                None,
                ctypes.byref(port_name_buffer),
                ctypes.byref(port_name_length))
            RegCloseKey(hkey)


            # unfortunately does this method also include parallel ports.
            # we could check for names starting with COM or just exclude LPT
            # and hope that other "unknown" names are serial ports...
            if port_name_buffer.value == "":
                continue
            if port_name_buffer.value.startswith('LPT'):
                continue
            if port_name_buffer.value.startswith('NULL_'):  # @@@ remove ports starting with NULL_
                continue
            if not port_name_buffer.value:  # @@@ remove ports without name
                continue

            # print('portname:{}'.format(port_name_buffer.value))
            all_ports.append(port_name_buffer.value)
    return all_ports