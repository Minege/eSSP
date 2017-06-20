#!/usr/bin/env python3
from ctypes import *
from time import sleep
from .constants import *

# CONSTANTS FOR SIGNALS AND COMMANDS

# C STRUCTURES

class SSP6_CHANNEL_DATA(Structure):
    _fields_ = [("security", c_ubyte),
            ("value", c_uint),
            ("cc", c_char*4)]

class SSP6_SETUP_REQUEST_DATA(Structure):
    _fields_ = [("UnitType", c_ubyte),
            ("FirmwareVersion", c_char*5),
            ("NumberOfChannels", c_uint),
            ("ChannelData", SSP6_CHANNEL_DATA*20),
            ("RealValueMultiplier", c_ulong),
            ("ProtocolVersion", c_ubyte)]

class SSP_POLL_EVENT6(Structure):
    _fields_ = [("event", c_ubyte),
            ("data1", c_ulong),
            ("data2", c_ulong),
            ("cc", c_char*4)]

class SSP_POLL_DATA6(Structure):
    _fields_ = [("events", SSP_POLL_EVENT6*20),
            ("event_count", c_ubyte)]

class eSSP:
    """Encrypted Smiley Secure Protocol Class"""
    def __init__(self, com_port, spp_address="0", nv11=False, debug=False):
        self.debug = debug
        self.nv11 = nv11
        self.actions = ""
        self.actions_args = {}
        self.response_data = {}
        self.response_data['getnoteamount_response'] = 9999 # There can't be 9999 notes in the storage
        self.sspC = self.essp.ssp_init(com_port.encode(), spp_address.encode(), debug)
        self.poll = SSP_POLL_DATA6()
        setup_req = SSP6_SETUP_REQUEST_DATA()
        #Check if the validator is present
        if self.essp.ssp6_sync(self.sspC) != SSP_RESPONSE_OK:
            self.print_debug("NO VALIDATOR FOUND")
            self.close()
            return False
        else:
            self.print_debug("Validator Found !")
        #Try to setup encryption
        if self.essp.ssp6_setup_encryption(self.sspC, c_ulonglong(0x123456701234567)) == SSP_RESPONSE_OK:
            self.print_debug("Encryption Setup")
        else:
            self.print_debug("Encryption Failed")

        #Checking the version, make sure we are using ssp version 6
        if self.essp.ssp6_host_protocol(self.sspC, 0x06) != SSP_RESPONSE_OK:
            self.print_debug(self.essp.ssp6_host_protocol(self.sspC, 0x06))
            self.print_debug("Host Protocol Failed")
            self.close()
            return False

        #Get some information about the validator
        if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != SSP_RESPONSE_OK:
            self.print_debug("Setup Request Failed")
            self.close()
            return False
        
        if self.debug:
            print("Firmware %s "%(setup_req.FirmwareVersion.decode('utf8')))
            print("Channels : ")
            for i,channel in enumerate(setup_req.ChannelData):
                print("Channel %s :  %s %s"%(str(i+1),str(channel.value),str(channel.cc)))

        #Enable the validator
        if self.essp.ssp6_enable(self.sspC) != SSP_RESPONSE_OK:
            self.print_debug("Enable Failed")
            self.close()
            return False

        if setup_req.UnitType == 0x03:
            for channel in enumerate(setup_req.ChannelData):
                self.essp.ssp6_set_coinmech_inhibits(self.sspC, channel.value, channel.cc, ENABLED)
        else:
            if setup_req.UnitType == 0x06 or setup_req.UnitType == 0x07:
                #Enable the payout unit
                if self.essp.ssp6_enable_payout(self.sspC, setup_req.UnitType) != SSP_RESPONSE_OK:
                    self.print_debug("Payout Enable Failed")
                    self.close()
                    return False

            # Set the inhibits ( enable all note acceptance )
            if self.essp.ssp6_set_inhibits(self.sspC,0xFF,0xFF) != SSP_RESPONSE_OK:
                self.print_debug("Inhibits Failed")
                self.close()
                return False

    def close(self):
        """Close the connection"""
        self.reject()
        self.essp.close_ssp_port()

    def reject(self):
        """Reject the bill if there is one"""
        if self.essp.ssp6_reject != SSP_RESPONSE_OK:
            self.print_debug("Error to reject bill OR nothing to reject")

    def do_actions(self):
        ACTION_SIZE = len(self.actions)
        i = 0
        while i < ACTION_SIZE:
            self.print_debug(self.actions)
            if self.actions[0] == "c": # Route to cashbox
                if self.essp.ssp6_set_route(self.sspC, self.actions_args['routec_amount'], self.actions_args['routec_currency'], ENABLED) != SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Route to cashbox failed")

            elif self.actions[0] == "s": # Route to storage
                if self.essp.ssp6_set_route(self.sspC, self.actions_args['routes_amount'], self.actions_args['routes_currency'], DISABLED) != SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Route to storage failed")

            elif self.actions[0] == "p": # Payout
                if self.essp.ssp6_payout(self.sspC, self.actions_args['payout_amount'], self.actions_args['payout_currency'], SSP6_OPTION_BYTE_DO) != SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Payout failed")
                    #Checking the error
                    response_data = cast(self.essp.ssp_get_response_data(self.sspC), POINTER(c_ubyte))
                    if response_data[1] == 0x01:
                        self.print_debug("Not enough value in Smart Payout")
                    elif response_data[1] == 0x02:
                        self.print_debug("Can't pay exact amount")
                    elif response_data[1] == 0x03:
                        self.print_debug("Smart Payout is busy")
                    elif response_data[1] == 0x04:
                        self.print_debug("Smart Payout is disabled")

            elif self.actions[0] == "y": # Payout next note ( NV11 only )
                self.print_debug("Payout next note")
                setup_req = SSP6_SETUP_REQUEST_DATA()
                if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != SSP_RESPONSE_OK:
                    self.print_debug("Setup Request Failed")
                if setup_req.UnitType != 0x07:
                    self.print_debug("Payout next note is only valid for NV11")
                if self.essp.ssp6_payout_note(self.sspC) != SSP_RESPONSE_OK:
                    self.print_debug("Payout next note failed")
                
            elif self.actions[0] == "z": # Stack next note ( NV11 only )
                setup_req = SSP6_SETUP_REQUEST_DATA()
                if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != SSP_RESPONSE_OK:
                    self.print_debug("Setup Request Failed")
                if setup_req.UnitType != 0x07:
                    self.print_debug("Payout next note is only valid for NV11")
                if self.essp.ssp6_stack_note(self.sspC) != SSP_RESPONSE_OK:
                    self.print_debug("Stack next note failed")
            
            elif self.actions[0] == "d": # Disable the validator
                if self.essp.ssp6_disable(self.sspC) != SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Disable failed")

            elif self.actions[0] == "D": # Disable the payout device
                if self.essp.ssp6_disable_payout(self.sspC) != SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Disable payout failed")

            elif self.actions[0] == "g": # Get the note amount
                if self.essp.ssp6_get_note_amount(self.sspC, self.actions_args['getnoteamount_amount'], self.actions_args['getnoteamount_currency']) != SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Can't read the note amount")
                    self.response_data['getnoteamount_response'] = 9999
                else:
                    response_data = cast(self.essp.ssp_get_response_data(self.sspC), POINTER(c_ubyte))
                    self.print_debug(response_data[1])
                    self.response_data['getnoteamount_response'] = response_data[1] # The number of note

            elif self.actions[0] == "E": # Empty the storage ( Send all to the cashbox )
                if self.essp.ssp6_empty(self.sspC) != SSP_RESPONSE_OK:
                    self.print_debug("ERROR: Can't empty the storage")
                else:
                    self.print_debug("Emptying, please wait...")
            self.__clean_actions_list()
            i+=1
            
    def __clean_actions_list(self):
        self.actions = self.actions[1:]

    def print_debug(self, text):
        if self.debug:
            print(text)

    def enable_validator(self):
        """Enable the validator"""
        setup_req = SSP6_SETUP_REQUEST_DATA()
        if self.essp.ssp6_enable(self.sspC) != SSP_RESPONSE_OK:
            self.print_debug("ERROR: Enable failed")
            return False
        #SMART Hopper requires different inhibit commands, so use setup request to see if it is an SH
        if self.essp.ssp6_setup_request(self.sspC, byref(setup_req)) != SSP_RESPONSE_OK:
            self.print_debug("Setup request failed")
            return False
        if setup_req.UnitType == 0x03:
            #SMART Hopper requires different inhibit commands
            for channel in setup_req.ChannelData:
                self.essp.ssp6_set_coinmech_inhibits(self.sspC, channel.value, channel.cc, ENABLED)
        else:
            if self.essp.ssp6_set_inhibits(self.sspC, 0xFF, 0xFF) != SSP_RESPONSE_OK:
                self.print_debug("Inhibits Failed")
                return False

    def parse_poll(self):
        """Parse the poll, for getting events"""
        for events in self.poll.events:
            if events.event == SSP_POLL_RESET:
                self.print_debug("Unit Reset")
                if self.essp.ssp6_host_protocol(self.sspC, 0x06) != SSP_RESPONSE_OK:
                    self.print_debug("Host Protocol Failed")
                    self.close()
                    return (0,0,events.event)
            elif events.event == SSP_POLL_READ:
                if events.data1 > 0:
                    self.print_debug("Note Read %s %s"%(events.data1,events.cc))
                    return (events.data1, events.cc, events.event)
            elif events.event == SSP_POLL_CREDIT:
                self.print_debug("Credit %s %s"%(events.data1,events.cc))
                return (events.data1, events.cc, events.event)
            elif events.event == SSP_POLL_INCOMPLETE_PAYOUT:
                self.print_debug("Incomplete payout %s of %s %s" % (events.data1,events.data2, events.cc))
                return (0,0,events.event)
            elif events.event == SSP_POLL_INCOMPLETE_FLOAT:
                self.print_debug("Incomplete float %s of %s %s"%(events.data1,events.data2,events.cc))
                return (0,0,events.event)
            elif events.event == SSP_POLL_REJECTING:
                # Do nothing
                return (0,0,events.event)
            elif events.event == SSP_POLL_REJECTED:
                self.print_debug("Note Rejected")
                return (0,0,events.event)
            elif events.event == SSP_POLL_STACKING:
                # Do nothing
                return (0,0,events.event)
            elif events.event == SSP_POLL_STORED:
                self.print_debug("Stored")
                return (0,0,events.event)
            elif events.event == SSP_POLL_STACKED:
                self.print_debug("Stacked")
                return (0,0,events.event)
            elif events.event == SSP_POLL_SAFE_JAM:
                self.print_debug("Safe Jam")
                return (0,0,events.event)
            elif events.event == SSP_POLL_UNSAFE_JAM:
                self.print_debug("Unsafe Jam")
                return (0,0,events.event)
            elif events.event == SSP_POLL_DISABLED:
                self.print_debug("VALIDATOR DISABLED")
                return (0,0,events.event)
            elif events.event == SSP_POLL_FRAUD_ATTEMPT:
                self.print_debug("Fraud Attempt %s %s"%(events.data1,events.cc))
                return (0,0,events.event)
            elif events.event == SSP_POLL_STACKER_FULL:
                self.print_debug("Stacker Full")
                return (0,0,events.event)
            elif events.event == SSP_POLL_CASH_BOX_REMOVED:
                self.print_debug("Cashbox Removed")
                return (0,0,events.event)
            elif events.event == SSP_POLL_CASH_BOX_REPLACED:
                self.print_debug("Cashbox Replaced")
                return (0,0,events.event)
            elif events.event == SSP_POLL_CLEARED_FROM_FRONT:
                self.print_debug("Cleared from front")
                return (0,0,events.event)
            elif events.event == SSP_POLL_CLEARED_INTO_CASHBOX:
                self.print_debug("Cleared into Cashbox")
                return (0,0,events.event)
            elif events.event == SSP_POLL_CALIBRATION_FAIL:
                self.print_debug("Calibration fail :")
                if events.data1 == NO_FAILUE:
                    self.print_debug("No failure")
                if events.data1 == SENSOR_FLAP:
                    self.print_debug("Optical sensor flap")
                if events.data1 == SENSOR_EXIT:
                    self.print_debug("Optical sensor exit")
                if events.data1 == SENSOR_COIL1:
                    self.print_debug("Coil sensor 1")
                if events.data1 == SENSOR_COIL2:
                    self.print_debug("Coil sensor 2")
                if events.data1 == NOT_INITIALISED:
                    self.print_debug("Unit not initialised")
                if events.data1 == CHECKSUM_ERROR:
                    self.print_debug("Data checksum error")
                if events.data1 == COMMAND_RECAL:
                    self.print_debug("Recalibration by command required")
                    self.essp.ssp6_run_calibration(self.sspC)
                return (0,0,events.event)
            elif events.event == SSP_POLL_EMPTYING:
                self.print_debug("Started emptying")
                return (0,0,events.event)
            elif events.event == SSP_POLL_EMPTY:
                self.print_debug("Finished emptying")
                return (0,0,events.event)

        return (0,0,NO_EVENT)

    def set_route_cashbox(self, amount, currency="CHF"):
        """Set the bills <amount> in the cashbox
           NV11: Set the bills <= amount in the cashbox"""
        #if not isinstance(currency, bytes):
        #    raise ValueError("Currency must be a byte buffer")
        self.actions+="c"
        self.actions_args['routec_amount'] = amount*100
        self.actions_args['routec_currency'] = currency.upper().encode()

    def set_route_storage(self, amount, currency="CHF"):
        """Set the bills <amount> in the storage
           NV11: Set the bills <= amount in the storage"""
        #if not isinstance(currency, bytes):
        #    raise ValueError("Currency must be a byte buffer")
        self.actions+="s"
        self.actions_args['routes_amount'] = amount*100
        self.actions_args['routes_currency'] = currency.upper().encode()

    def payout(self, amount, currency="CHF"):
        """Payout note(s) for completing the amount passed in parameter"""
        #if not isinstance(currency, bytes):
        #    raise ValueError("Currency must be a byte buffer")
        self.actions+="p"
        self.actions_args['payout_amount'] = amount*100
        self.actions_args['payout_currency'] = currency.upper().encode()

    def get_note_amount(self, amount, currency="CHF"):
        """Payout note(s) for completing the amount passed in parameter"""
        #if not isinstance(currency, bytes):
        #    raise ValueError("Currency must be a byte buffer")
        self.actions+="g"
        self.actions_args['getnoteamount_amount'] = amount*100
        self.actions_args['getnoteamount_currency'] = currency.upper().encode()

    def reset(self):
        self.print_debug("Starting reset")
        self.essp.ssp6_reset(self.sspC)
        self.print_debug("Reset complet")

    def nv11_payout(self):
        self.actions+="y"

    def nv11_stack(self): 
        self.actions+="z"
 
    def empty_storage(self):
        self.actions+="E"

    def disable_payout(self):
        self.actions+="D"

    def disable_validator(self):
        self.actions+="d"
