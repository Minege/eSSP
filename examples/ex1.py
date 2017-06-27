import threading
from eSSP.constants import *
from eSSP import eSSP  # Import the library
from ctypes import *
from time import sleep

validator = eSSP(com_port="/dev/ttyUSB0", spp_address="0", nv11=False, debug=True)  # Create a new object ( Validator Object ) and initialize it ( In debug mode, so it will print debug infos )

def event_loop():
    while(1):
                    # ---- Example of interaction with events ---- #
        if validator.nv11: # If the model is an NV11, put every 100 note in the storage, and others in the stack(cashbox), but that's just for this example
            (note, currency,event) = validator.get_last_event()
            if note == 0 or currency == 0 or event == 0:
                pass # Operation that do not send money info, we don't do anything with it
            else:
                if note != 4 and event == Status.SSP_POLL_CREDIT:
                    validator.print_debug("NOT A 100 NOTE")
                    validator.nv11_stack_next_note()
                    validator.enable_validator()
                elif note == 4 and event == Status.SSP_POLL_READ:
                    validator.print_debug("100 NOTE")
                    validator.set_route_storage(100) # Route to storage
                    validator.do_actions()
                    validator.set_route_cashbox(50) # Everything under or equal to 50 to cashbox ( NV11 )
        sleep(0.5)

t1 = threading.Thread(target=event_loop)  # Create a new thread on the Validator System Loop ( needed for the signal )
t1.setDaemon(True)  # Set the thread as daemon because it don't catch the KeyboardInterrupt, so it will stop when we cut the main thread
t1.start()  # Start the validator system loop thread ( Needed for starting sending action )

try: # Command Interpreter
    while(1):
        choice = input("")
        if choice=="p":  # Payout "choice" value bill ( 10, 20, 50, 100, etc. )
            choice = input("")
            validator.payout(int(choice))
        elif choice == "s":  # Route to cashbox ( In NV11, it is any amount <= than "choice" )
            choice = input("")
            validator.set_route_storage(int(choice))
        elif choice == "c":  # Route to cashbox ( In NV11, it is any amount <= than "choice" )
            choice = input("")
            validator.set_route_cashbox(int(choice))
        elif choice == "e":  # Enable ( Automaticaly disabled after a payout )
            validator.enable_validator()
        elif choice == "r":  # Reset ( It's like a "reboot" of the validator )
            validator.reset()
        elif choice == "y":  # NV11 Payout last entered ( next available )
            print("Payout next 1")
            validator.nv11_payout_next_note()
        elif choice == "d":  # Disable
            validator.disable_validator()
        elif choice == "D": # Disable the payout device
            validator.disable_payout()
        elif choice == "E": # Empty the storage to the cashbox
            validator.empty_storage()
        elif choice == "g": # Get the number of bills denominated with their values
            choice = input("")
            validator.get_note_amount(int(choice))
            sleep(1)
            print("Number of bills of %s : %s"%(choice, validator.response_data['getnoteamount_response']))

except KeyboardInterrupt: # If user do CTRL+C
    validator.close() # Close the connection with the validator
    print("Exiting")
    exit(0)
