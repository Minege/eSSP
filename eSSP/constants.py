from aenum import Enum

class Status(Enum):
    _init_ = 'value', 'debug_message'

    SSP_RESPONSE_ERROR = 0xFF, "Error"
    SSP_RESPONSE_TIMEOUT = 0xFF, "Timeout"
    SSP_RESPONSE_OK = 0xF0, "Ok"
    ENABLED = 0x01, "Enabled"
    DISABLED = 0x00, "Disabled"
    SSP_POLL_RESET = 0xF1, "Poll Reset"
    SSP_POLL_READ = 0xEF, "Read note" #next byte is channel (0 for unknown)
    SSP_POLL_CREDIT = 0xEE, "Credit note" #next byte is channel
    SSP_POLL_REJECTING = 0xED, "Reject"
    SSP_POLL_REJECTED = 0xEC, "Rejected"
    SSP_POLL_STACKING = 0xCC, "Stacking"
    SSP_POLL_STACKED = 0xEB, "Stacked"
    SSP_POLL_SAFE_JAM = 0xEA, "Safe Jam"
    SSP_POLL_UNSAFE_JAM = 0xE9, "Unsafe Jam"
    SSP_POLL_DISABLED = 0xE8, "Poll Disabled"
    SSP_POLL_FRAUD_ATTEMPT = 0xE6, "Fraud Attempt" #next byte is channel
    SSP_POLL_STACKER_FULL = 0xE7, "Stacker Full"
    SSP_POLL_CLEARED_FROM_FRONT = 0xE1, "Cleared from front"
    SSP_POLL_CLEARED_INTO_CASHBOX = 0xE2, "Cleared into cashbox"
    SSP_POLL_BARCODE_VALIDATE = 0xE5, "Barcode Validate"
    SSP_POLL_BARCODE_ACK = 0xD1, "Barcode ACK"
    SSP_POLL_CASH_BOX_REMOVED = 0xE3, "Cashbox Removed"
    SSP_POLL_CASH_BOX_REPLACED = 0xE4, "Cashbox Replaced"
    SSP_POLL_DISPENSING = 0xDA, "Dispensing"
    SSP_POLL_DISPENSED = 0xD2, "Dispensed"
    SSP_POLL_JAMMED = 0xD5, "Jammed"
    SSP_POLL_HALTED = 0xD6, "Halted"
    SSP_POLL_FLOATING = 0xD7, "Floating"
    SSP_POLL_FLOATED = 0xD8, "Floated"
    SSP_POLL_TIMEOUT = 0xD9, "Timeout"
    SSP_POLL_INCOMPLETE_PAYOUT = 0xDC, "Incomplete Payout"
    SSP_POLL_INCOMPLETE_FLOAT = 0xDD, "Incomplete Float"
    SSP_POLL_CASHBOX_PAID = 0xDE, "Cashbox paid"
    SSP_POLL_COIN_CREDIT = 0xDF, "Coin credit"
    SSP_POLL_EMPTYING = 0xC2, "Emptying"
    SSP_POLL_EMPTY = 0xC3, "Empty"
    SSP_POLL_COINS_LOW = 0xD3, "Coins low"
    SSP_POLL_COINS_EMPTY = 0xD4, "Coins empty"
    SSP_POLL_CALIBRATION_FAIL = 0x83, "Calibration Failed"
    SSP_POLL_SMART_EMPTYING = 0xB3, "Smart emptying"
    SSP_POLL_SMART_EMPTIED = 0xB4, "Smart emptied"
    SSP_POLL_STORED = 0xDB, "Stored"
    SSP6_OPTION_BYTE_DO = 0x58, "Option Byte DO"
    NO_EVENT = 0xF9, "No event"
    SMART_PAYOUT_NOT_ENOUGH = 0x01, "Not enough value in smart payout"
    SMART_PAYOUT_EXACT_AMOUNT = 0x02, "Can't pay exact amount"
    SMART_PAYOUT_BUSY = 0x03, "Smart payout is busy"
    SMART_PAYOUT_DISABLED = 0x04, "Smart payout is disabled"

    # def __init__(self, code, debug_message):
        # self.code = code
        # self.debug_message = debug_message

    def __int__(self):
        return self.value

    def __str__(self):
        return self.debug_message

    def __eq__(self, other):
        return self.value == other
    
    def __ne__(self, other):
        return self.value != other

class FailureStatus(Enum):
    _init_ = 'value', 'debug_message'

    NO_FAILUE = 0x00, "No Failure"
    SENSOR_FLAP = 0x01, "Optical Sensor Flap"
    SENSOR_EXIT = 0x02, "Optical Sensor Exit"
    SENSOR_COIL1 = 0x03, "Coil sensor 1"
    SENSOR_COIL2 = 0x04, "Coil sensor 2"
    NOT_INITIALISED = 0x05, "Unit not initialized"
    CHECKSUM_ERROR = 0x06, "Data checksum error"
    COMMAND_RECAL = 0x07, "Recalibration by command required"

    def __int__(self):
        return self.value

    def __str__(self):
        return self.debug_message

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

class Actions(Enum):
    _init_ = 'value', 'debug_message'

    ROUTE_TO_CASHBOX = 0, "Route to cashbox"
    ROUTE_TO_STORAGE = 1, "Route to storage"
    PAYOUT = 2, "Payout"
    PAYOUT_NEXT_NOTE_NV11 = 3, "Payout next note"
    STACK_NEXT_NOTE_NV11 = 4, "Stack next note"
    DISABLE_VALIDATOR = 5, "Disable validator"
    DISABLE_PAYOUT = 6, "Disable payout"
    GET_NOTE_AMOUNT = 7, "Get note amount"
    EMPTY_STORAGE = 8, "Empty storage & cleaning indexes"

    # def __init__(self, code, debug_message):
        # self.code = code
        # self.debug_message = debug_message

    def __int__(self):
        return self.value

    def __str__(self):
        return self.debug_message

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

if __name__ == "__main__":
    print(FailureStatus.SENSOR_FLAP == 1)
    print(FailureStatus(1))
