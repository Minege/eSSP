import threading
from eSSP.eSSP import *  # Import the library

validator = eSSP(com_port="/dev/ttyACM0", spp_address="0", nv11=False, debug=True)  # Create a new object ( Validator Object ) and initialize it ( In debug mode, so it will print debug infos )

def system_loop(): # Looping for getting the alive signal
    while(1):
        rsp_status = validator.essp.ssp6_poll(validator.sspC, byref(validator.poll)) # Get the pool
        if rsp_status != SSP_RESPONSE_OK: # If there's a problem, check wath is it
            if rsp_status == SSP_RESPONSE_TIMEOUT: # Timeout
                validator.print_debug("SSP Poll Timeout")
                validator.close()
                exit(0)
            else:
                if rsp_status == 0xFA:
                    #The validator has responded with key not set, so we should try to negotiate one
                    if validator.essp.ssp6_setup_encryption(validator.sspC, c_ulonglong(0x123456701234567)) == SSP_RESPONSE_OK:
                        validator.print_debug("Encryption Setup")
                    else:
                        validator.print_debug("Encryption Failed")

                else:
                    validator.print_debug("SSP Poll Error",rsp_status) # Not theses two, stop the program
                    return False


                    # ---- Example of interaction with events ---- #
        if validator.nv11: # If the model is an NV11, interact specially with the poll, but that's just for this example
            (note, currency,event) = validator.parse_poll() # Get event
            if note == 0 or currency == 0 or event == 0:
                pass # Operation that do not send money info, we don't do anything with it
            else:
                if note != 4 and event == SSP_POLL_CREDIT:
                    validator.print_debug("NOT A 100 NOTE")
                    validator.nv11_stack()
                    validator.enable_validator()
                elif note == 4 and event == SSP_POLL_READ:
                    validator.print_debug("100 NOTE")
                    validator.set_route_storage(100) # Route to storage
                    validator.do_actions()
                    validator.set_route_cashbox(50) # Everything under or equal to 50 to cashbox ( NV11 )

            validator.do_actions()
                    # ---- *** ---- #


        else: # NV200 or something else, do this ( regular read of events, can also interact with them )
            validator.parse_poll()
            validator.do_actions()
        sleep(0.5)

t1 = threading.Thread(target=system_loop)  # Create a new thread on the Validator System Loop ( needed for the signal )
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
            validator.nv11_payout()
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
