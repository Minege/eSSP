# !/usr/bin/env python3
from ctypes import *
from time import sleep
import threading
from six.moves import queue

from .constants import Status, Actions


class Ssp6ChannelData(Structure):
    _fields_ = [("security", c_ubyte),
                ("value", c_uint),
                ("cc", c_char*4)]


class Ssp6SetupRequestData(Structure):
    _fields_ = [("UnitType", c_ubyte),
                ("FirmwareVersion", c_char*5),
                ("NumberOfChannels", c_uint),
                ("ChannelData", Ssp6ChannelData*20),
                ("RealValueMultiplier", c_ulong),
                ("ProtocolVersion", c_ubyte)]


class SspPollEvent6(Structure):
    _fields_ = [("event", c_ubyte),
                ("data1", c_ulong),
                ("data2", c_ulong),
                ("cc", c_char*4)]


class SspPollData6(Structure):
    _fields_ = [("events", SspPollEvent6*20),
                ("event_count", c_ubyte)]


class eSSP(object):
    """Encrypted Smiley Secure Protocol Class"""
    def __init__(self, com_port, spp_address="0", nv11=False, debug=False):
        self.debug = debug
        self.nv11 = nv11
        self.actions = queue.Queue()
        self.actions_args = {}
        self.response_data = {}
        self.events = []
        self.response_data['getnoteamount_response'] = 9999  # There can't be 9999 notes in the storage
        self.sspC = self.essp.Status.SSP_init(com_port.encode(), spp_address.encode(), debug)
        self.poll = SspPollData6()
        setup_req = Ssp6SetupRequestData()
        # Check if the validator is present
        if self.essp.ssp6_sync(self.sspC) != Status.SSP_RESPONSE_OK:
            self.print_debug("NO VALIDATOR FOUND")
            self.close()
        else:
            self.print_debug("Validator Found !")
        # Try to setup encryption
        if self.essp.ssp6_setup_encryption(self.sspC, c_ulonglong(0x123456701234567)) == Status.SSP_RESPONSE_OK:
            self.print_debug("Encryption Setup")
        else:
            self.print_debug("Encryption Failed")

        # Checking the version, make sure we are using ssp version 6
        if self.essp.ssp6_host_protocol(self.sspC, 0x06) != Status.SSP_RESPONSE_OK:
            self.print_debug(self.essp.ssp6_host_protocol(self.sspC, 0x06))
            self.print_debug("Host Protocol Failed")
            self.close()

        # Get some information about the validator
        if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != Status.SSP_RESPONSE_OK:
            self.print_debug("Setup Request Failed")
            self.close()

        if self.debug:
            print("Firmware %s " % (setup_req.FirmwareVersion.decode('utf8')))
            print("Channels : ")
            for i,channel in enumerate(setup_req.ChannelData):
                print("Channel %s :  %s %s" % (str(i+1), str(channel.value), channel.cc.decode()))

        # Enable the validator
        if self.essp.ssp6_enable(self.sspC) != Status.SSP_RESPONSE_OK:
            self.print_debug("Enable Failed")
            self.close()

        if setup_req.UnitType == 0x03:
            for channel in enumerate(setup_req.ChannelData):
                self.essp.ssp6_set_coinmech_inhibits(self.sspC, channel.value, channel.cc, Status.ENABLED)
        else:
            if setup_req.UnitType == 0x06 or setup_req.UnitType == 0x07:
                # Enable the payout unit
                if self.essp.ssp6_enable_payout(self.sspC, setup_req.UnitType) != Status.SSP_RESPONSE_OK:
                    self.print_debug("Payout Enable Failed")
                    self.close()

            # Set the inhibits ( enable all note acceptance )
            if self.essp.ssp6_set_inhibits(self.sspC, 0xFF, 0xFF) != Status.SSP_RESPONSE_OK:
                self.print_debug("Inhibits Failed")
                self.close()
        t1 = threading.Thread(target=self.system_loop)
        t1.start()

    def close(self):
        """Close the connection"""
        self.reject()
        self.essp.close_ssp_port()

    def reject(self):
        """Reject the bill if there is one"""
        if self.essp.ssp6_reject != Status.SSP_RESPONSE_OK:
            self.print_debug("Error to reject bill OR nothing to reject")

    def do_actions(self):
        while self.actions:
            action = self.actions.get()  # get and delete
            self.print_debug(Actions.action)
            if action == Actions.ROUTE_TO_CASHBOX:  # Route to cashbox
                if self.essp.ssp6_set_route(self.sspC, self.actions_args['routec_amount'], self.actions_args['routec_currency'], Status.ENABLED) != Status.SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Route to cashbox failed")

            elif action == Actions.ROUTE_TO_STORAGE:  # Route to storage
                if self.essp.ssp6_set_route(self.sspC, self.actions_args['routes_amount'], self.actions_args['routes_currency'], Status.ENABLED) != Status.SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Route to storage failed")

            elif action == Actions.PAYOUT:  # Payout
                if self.essp.ssp6_payout(self.sspC, self.actions_args['payout_amount'], self.actions_args['payout_currency'], Status.SSP6_OPTION_BYTE_DO) != Status.SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Payout failed")
                    # Checking the error
                    response_data = cast(self.essp.Status.SSP_get_response_data(self.sspC), POINTER(c_ubyte))
                    if response_data[1] == 0x01:
                        self.print_debug("Not enough value in Smart Payout")
                    elif response_data[1] == 0x02:
                        self.print_debug("Can't pay exact amount")
                    elif response_data[1] == 0x03:
                        self.print_debug("Smart Payout is busy")
                    elif response_data[1] == 0x04:
                        self.print_debug("Smart Payout is Status.ENABLED")

            elif action == Actions.PAYOUT_NEXT_NOTE_NV11:  # Payout next note ( NV11 only )
                self.print_debug("Payout next note")
                setup_req = Ssp6SetupRequestData()
                if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != Status.SSP_RESPONSE_OK:
                    self.print_debug("Setup Request Failed")
                if setup_req.UnitType != 0x07:
                    self.print_debug("Payout next note is only valid for NV11")
                if self.essp.ssp6_payout_note(self.sspC) != Status.SSP_RESPONSE_OK:
                    self.print_debug("Payout next note failed")
                
            elif action == Actions.STACK_NEXT_NOTE_NV11:  # Stack next note ( NV11 only )
                setup_req = Ssp6SetupRequestData()
                if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != Status.SSP_RESPONSE_OK:
                    self.print_debug("Setup Request Failed")
                if setup_req.UnitType != 0x07:  # Maybe the version,  or something ( taken from the SDK C code )
                    self.print_debug("Payout next note is only valid for NV11")
                if self.essp.ssp6_stack_note(self.sspC) != Status.SSP_RESPONSE_OK:
                    self.print_debug("Stack next note failed")
            
            elif action == Actions.DISABLE_VALIDATOR:  # Disable the validator
                if self.essp.ssp6_disable(self.sspC) != Status.SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Disable failed")

            elif action == Actions.DISABLE_PAYOUT:  # Disable the payout device
                if self.essp.ssp6_disable_payout(self.sspC) != Status.SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Disable payout failed")

            elif action == Actions.GET_NOTE_AMOUNT:  # Get the note amount
                if self.essp.ssp6_get_note_amount(self.sspC, self.actions_args['getnoteamount_amount'], self.actions_args['getnoteamount_currency']) != Status.SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Can't read the note amount")
                    self.response_data['getnoteamount_response'] = 9999  # There can't be 9999 notes
                else:
                    response_data = cast(self.essp.Status.SSP_get_response_data(self.sspC), POINTER(c_ubyte))
                    self.print_debug(response_data[1])
                    self.response_data['getnoteamount_response'] = response_data[1]  # The number of note

            elif action == Actions.EMPTY_STORAGE:  # Empty the storage ( Send all to the cashbox )
                if self.essp.ssp6_empty(self.sspC) != Status.SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Can't empty the storage")
                else:
                    self.print_debug("Emptying, please wait...")

    def print_debug(self, text):
        if self.debug:
            print(text)

    def enable_validator(self):
        """Enable the validator"""
        setup_req = Ssp6SetupRequestData()
        if self.essp.ssp6_enable(self.sspC) != Status.SSP_RESPONSE_OK:
            self.print_debug("ERROR: Enable failed")
            return False
        # SMART Hopper requires different inhibit commands, so use setup request to see if it is an SH
        if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != Status.SSP_RESPONSE_OK:
            self.print_debug("Setup request failed")
            return False
        if setup_req.UnitType == 0x03:
            # SMART Hopper requires different inhibit commands
            for channel in setup_req.ChannelData:
                self.essp.ssp6_set_coinmech_inhibits(self.sspC, channel.value, channel.cc, Status.ENABLED)
        else:
            if self.essp.ssp6_set_inhibits(self.sspC, 0xFF, 0xFF) != Status.SSP_RESPONSE_OK:
                self.print_debug("Inhibits Failed")
                return False

    def parse_poll(self):
        """Parse the poll, for getting events"""

        for events in self.poll.events:
            try:
                self.print_debug(Status.events.event)
            except ValueError:
                self.print_debug('Unknown status: {}'.format(events.event))

            if events.event == Status.SSP_POLL_RESET:
                self.print_debug("Unit Reset")
                if self.essp.ssp6_host_protocol(self.sspC, Status.CHECKSUM_ERROR) != Status.SSP_RESPONSE_OK:
                    self.print_debug("Host Protocol Failed")
                    self.close()

            elif events.event == Status.SSP_POLL_READ:
                if events.data1 > 0:
                    self.print_debug("Note Read %s %s" % (events.data1, events.cc.decode()))
                    return events.data1, events.cc.decode(), events.event

            elif events.event == Status.SSP_POLL_CREDIT:
                self.print_debug("Credit %s %s" % (events.data1, events.cc.decode()))
                return events.data1, events.cc.decode(), events.event

            elif events.event == Status.SSP_POLL_INCOMPLETE_PAYOUT:
                self.print_debug("Incomplete payout %s of %s %s" % (events.data1, events.data2, events.cc.decode()))

            elif events.event == Status.SSP_POLL_INCOMPLETE_FLOAT:
                self.print_debug("Incomplete float %s of %s %s" % (events.data1, events.data2, events.cc.decode()))

            elif events.event == Status.SSP_POLL_FRAUD_ATTEMPT:
                self.print_debug("Fraud Attempt %s %s" % (events.data1, events.cc.decode()))
                return events.data1, events.cc.decode(), events.event

            elif events.event == Status.SSP_POLL_CALIBRATION_FAIL:
                self.print_debug("Calibration fail :")
                if events.data1 == Status.NO_FAILUE:
                    self.print_debug("No failure")
                if events.data1 == Status.SENSOR_FLAP:
                    self.print_debug("Optical sensor flap")
                if events.data1 == Status.SENSOR_EXIT:
                    self.print_debug("Optical sensor exit")
                if events.data1 == Status.SENSOR_COIL1:
                    self.print_debug("Coil sensor 1")
                if events.data1 == Status.SENSOR_COIL2:
                    self.print_debug("Coil sensor 2")
                if events.data1 == Status.NOT_INITIALISED:
                    self.print_debug("Unit not initialised")
                if events.data1 == Status.CHECKSUM_ERROR:
                    self.print_debug("Data checksum error")
                if events.data1 == Status.COMMAND_RECAL:
                    self.print_debug("Recalibration by command required")
                    self.essp.ssp6_run_calibration(self.sspC)

            return 0, 0, Status.events.event
        return 0, 0, Status.NO_EVENT

    def system_loop(self):  # Looping for getting the alive signal ( obligation in eSSP6 )
        while True:
            rsp_status = self.essp.ssp6_poll(self.sspC, byref(self.poll)) # Get the pool
            if rsp_status != Status.SSP_RESPONSE_OK: # If there's a problem, check wath is it
                if rsp_status == Status.SSP_RESPONSE_TIMEOUT: # Timeout
                    self.print_debug("SSP Poll Timeout")
                    self.close()
                    exit(0)
                else:
                    if rsp_status == 0xFA:
                        # The self has responded with key not set, so we should try to negotiate one
                        if self.essp.ssp6_setup_encryption(self.sspC, c_ulonglong(0x123456701234567)) == Status.SSP_RESPONSE_OK:
                            self.print_debug("Encryption Setup")
                        else:
                            self.print_debug("Encryption Failed")

                    else:
                        self.print_debug("SSP Poll Error", rsp_status)  # Not theses two, stop the program
                        return False
            self.events.append(self.parse_poll())
            self.do_actions()
            sleep(0.5)

    def get_last_event(self):
        """Get the last event and delete it from the event list"""
        event = self.events[len(self.events)-1]
        self.events.pop(len(self.events)-1)
        return event

    def __action_helper(self, amount, currency, action, prefix):
        self.actions.put(action)
        self.actions_args['{}_amount'.format(prefix)] = amount*100  # TODO: This is one action at time, also, i think that the validator can receive one type of command at time, so to implement : user can send multiple request without waiting, but we store them and process them every time we send to the validator ( 0.5, 0.5, 0.5, etc. )
        self.actions_args['{}_currency'.format(prefix)] = currency.upper().encode()

    def set_route_cashbox(self, amount, currency="CHF"):
        """Will set the route of <amount> in the cashbox
           NV11: Will set the route of <= amount in the cashbox"""
        self.__action_helper(amount, currency, Actions.ROUTE_TO_CASHBOX, "routec")

    def set_route_storage(self, amount, currency="CHF"):
        """Set the bills <amount> in the storage
           NV11: Set the bills <= amount in the storage"""
        self.__action_helper(amount, currency, Actions.ROUTE_STORAGE, "routes")

    def payout(self, amount, currency="CHF"):
        """Payout note(s) for completing the amount passed in parameter"""
        self.__action_helper(amount, currency, Actions.PAYOUT, "payout")

    def get_note_amount(self, amount, currency="CHF"):
        """Payout note(s) for completing the amount passed in parameter"""
        self.__action_helper(amount, currency, Actions.GET_NOTE_AMOUNT, "getnoteamount")

    def reset(self):
        self.print_debug("Starting reset")
        self.essp.ssp6_reset(self.sspC)
        self.print_debug("Reset complet")

    def nv11_payout_next_note(self):
        self.actions.put(Actions.PAYOUT_NEXT_NOTE_NV11)

    def nv11_stack_next_note(self):
        self.actions.put(Actions.STACK_NEXT_NOTE_NV11)
 
    def empty_storage(self):
        self.actions.put(Actions.EMPTY_STORAGE)

    def disable_payout(self):
        self.actions.put(Actions.DISABLE_PAYOUT)

    def disable_validator(self):
        self.actions.put(Actions.DISABLE_VALIDATOR)
