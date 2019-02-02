#! /usr/bin/env python3
name = "dxl"
import glob
from dynamixel_sdk import *
from reg import *


def get_available_ports():
    """
    Displays the ports connected to serial devices.
    Uses glob.glob object to return a tuple of possible serial ports.
    If no device is connected it returns None.
    Returns:
        A tuple containing ports with serial devices connected to them.
    """

    return (
        glob.glob("/dev/ttyUSB*")
        + glob.glob("/dev/ttyACM*")
        + glob.glob("/dev/ttyCOM*")
    )


class dxl(object):
    """
    Enables operations on dynamixel motors
    Attributes:
        portHandler: porthandler object from Dynamixel SDK
        packetHandler: packethandler object from Dynamixel SDK
    """

    def __init__(self, DeviceName, baudrate, protocol=1, mx=False):
        self.portHandler = PortHandler(DeviceName)
        self._baudrate = baudrate
        self._protocol_version = protocol
        self.packetHandler = PacketHandler(self.PROTOCOL_VERSION)

        try:
            assert self.portHandler.openPort()
            print("Opened port successfully")
        except AssertionError:
            print("Failed to open port")

        try:
            assert self.portHandler.setBaudRate(self.BAUDRATE)
            print("Changed baudrate successfully")
        except AssertionError:
            print("Failed to change baudrate")

        if protocol == 1:
            if mx:
                self._register = protocol1_mx
            else:
                self._register = protocol1
        else:
            self._register = protocol2

    @property
    def BAUDRATE(self):
        return self._baudrate

    @BAUDRATE.setter
    def BAUDRATE(self, baudrate):
        self._baudrate = baudrate
        return True

    @property
    def PROTOCOL_VERSION(self):
        return self._protocol_version

    @PROTOCOL_VERSION.setter
    def PROTOCOL_VERSION(self, protocol):
        try:
            assert protocol == 1 or protocol == 2
            self._protocol_version = protocol
        except AssertionError:
            print("Only Protocol 1 and Protocol 2 supported")
        return True

    def error(self, dxl_comm_result, dxl_error=0):
        """
        Displays the error output
        Args:
            dxl_comm_result: Communication result
            dxl_error: Error ID
        Returns:
            Boolean value depicting if there was an error or not
        """

        if dxl_comm_result is not COMM_SUCCESS:
            print(self.packetHandler.getTxRxResult(dxl_comm_result))
            return True
        elif dxl_error is not 0:
            print(self.getRxPacketError(dxl_error))
            return True
        return False

    def scan(self, ran=254):
        """
        Scans the given device for connected dynamixel motors
        Uses ping to determine which motor IDs are present.
        Args:
            ran: Range of values till which motors are pinged
        Return:
            List containing IDs of present motors
        """

        __ids = []
        for i in range(ran):
            dxl_model, dxl_comm_result, dxl_error = self.packetHandler.ping(
                self.portHandler, i
            )
            if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
                pass
            else:
                __ids.append(i)
        return __ids

    def read(self, DXL_ID):
        """
        Reads a given value in the control table from the specified motor.
        Args:
            DXL_ID: Motor ID
            data: string having data name from control table
        Returns:
            Present value at the given position
        """
        param1024 = "Present Position"
        pos = self._register[param1024][0]
        size = self._register[param1024][1]
        if size == 1:
            func = self.packetHandler.read1ByteTxRx
        elif size == 2:
            func = self.packetHandler.read2ByteTxRx
        else:
            func = self.packetHandler.read4ByteTxRx
        present_val, dxl_comm, dxl_error = func(self.portHandler, DXL_ID, pos)
        if not self.error(dxl_comm, dxl_error):
            return present_val
        else:
            return None

    def __write(self, DXL_ID, data, value):
        pos = self._register[data][0]
        size = self._register[data][1]
        if size == 1:
            func = self.packetHandler.write1ByteTxRx
        elif size == 2:
            func = self.packetHandler.write2ByteTxRx
        else:
            func = self.packetHandler.write4ByteTxRx
        dxl_comm, dxl_error = func(self.portHandler, DXL_ID, pos, value)
        if not self.error(dxl_comm, dxl_error):
            return True
        else:
            return False

    def move(self, DXL_ID, value):
        """
        Writes the given angle to the specified motor.
        Args:
            DXL_ID: Motor ID
            value: The angle to be moved to. 
        Returns:
            The motor moves to the specified angle.
        """
        data = "Goal Position"
        self.__write(DXL_ID, data, value)

    @staticmethod
    def create4ByteArray(bin_value):
        byte_array = [DXL_LOBYTE(DXL_LOWORD(bin_value)), DXL_HIBYTE(DXL_LOWORD(bin_value)), DXL_LOBYTE(DXL_HIWORD(bin_value)), DXL_HIBYTE(DXL_HIWORD(bin_value))]
        return byte_array

    @staticmethod
    def create2ByteArray(bin_value):
        byte_array = [
            DXL_LOBYTE(DXL_LOWORD(bin_value)),
            DXL_HIBYTE(DXL_LOWORD(bin_value)),
        ]
        return byte_array

    @staticmethod
    def create1ByteArray(bin_value):
        byte_array = [DXL_LOBYTE(DXL_LOWORD(bin_value))]
        return byte_array

    def __sync_write(self, param, ids):
        pos = self._register[param][0]
        size = self._register[param][1]
        groupSyncWrite = GroupSyncWrite(self.portHandler, self.packetHandler, pos, size)
        for k, v in ids.items():
            if size == 2:
                dxl_addparam_result = groupSyncWrite.addParam(
                    k, self.create2ByteArray(v)
                )
            elif size ==1:
                dxl_addparam_result = groupSyncWrite.addParam(
                    k, self.create1ByteArray(v)
                )
            else:
                dxl_addparam_result = groupSyncWrite.addParam(
                    k, self.create4ByteArray(v)
                )
            assert dxl_addparam_result, "Group Sync Write Failed"
        dxl_comm_result = groupSyncWrite.txPacket()
        assert self.error(dxl_comm_result) == False, "GroupSync Failed"

    def set_torque(self, ids):
        self.__sync_write("Torque Enable", ids)

    def set_speed(self, ids):
        self.__sync_write("Moving Speed", ids)

    def set_goal_position(self, ids):
        """
        Writes a set of angles to a group of motors so they move in sync.
        Args:
            ids: dictionary with the motor ID corresponding with the angle to be moved by.
        Returns:
            Moves the specified motors in sync.
        """
        param = "Goal Position"
        self.__sync_write(param, ids)

    def speed(self, DXL_ID, speed):
        """
        Sets the speed by which the specified motor has to move. 
        Args:
            DXL_ID: Motor ID
            speed: the value of the speed to be given.
        Returns:
            Moves the specified motor by the given speed when written on.
        """
        param = "Moving Speed"
        pos = self._register[param][0]
        size = self._register[param][1]
        if size == 1:
            func = self.packetHandler.write1ByteTxRx
        elif size == 2:
            func = self.packetHandler.write2ByteTxRx
        else:
            func = self.packetHandler.write4ByteTxRx
        dxl_comm, dxl_error = func(self.portHandler, DXL_ID, pos, speed)
        if not self.error(dxl_comm, dxl_error):
            return True
        else:
            return False

