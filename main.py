import time
from PyInquirer import prompt
from examples import custom_style_2, custom_style_1
from wallet import Wallet
from operation import Operation
from data import read_data, write_data
import os

import binascii
from prompt_toolkit.validation import Validator, ValidationError

wallets: [Wallet] = read_data()
operations: [Operation] = []

class NumberValidator(Validator):
    def validate(self, document):
        try:
            float(document.text)
        except ValueError:
            raise ValidationError(
                message="Please enter a number", cursor_position=len(document.text)
            )
os.system('clear')

def read_log() -> [str]:
    log_entries = []
    try:
        with open("log.txt", "r") as log_file:
            log_entries = log_file.readlines()
    except FileNotFoundError:
        print("Log file not found.")
    return log_entries


def main(console='clear'):
    questions = [
        {
            'type': 'list',
            'name': 'user_option',
            'message': 'Volume Bot',
            'choices': ["Wallets", "Add Wallet", "Add Token", "LOGS"]
        }
    ]
    
    def start_operation(wallet: Wallet):
        start_operation_questions = [
            {
                'type': 'input',
                'name': 'operation_target',
                'message': 'Token Address:',
            },
            {
                'type': 'input',
                'name': 'operation_bnb',
                'message': 'BNB Amount to spend:',
                'validate': NumberValidator()
            },
            {
                'type': 'input',
                'name': 'operation_buy_price',
                'message': 'BUY token at PRICE (on BNB):',
                'validate':  NumberValidator()
            },
            {
                'type': 'input',
                'name': 'operation_sell_price',
                'message': 'SELL token at PRICE (on BNB):',
                'validate':  NumberValidator()
            },
        ]
        answers = prompt(start_operation_questions, style=custom_style_2)
        try:
            operation = Operation(wallet=wallet, token_address=answers['operation_target'], wbnb_amount=answers['operation_bnb'], price_buy=float(answers['operation_buy_price']), price_sell=float(answers['operation_sell_price']))
            operations.append(operation)
            operation.start()
    
        except Exception as e:
            if str(e) == "Price Buy Can't be equal to or higher than Sell!":
                print("\n\033[31mError: Price Buy Can't be equal to or higher than Sell!\033[0m\n")
                start_operation(wallet)
        print("\n\n\n")
        time.sleep(4)
       

    def store_wallet():
        add_wallet_questions = [
            {
                'type': 'input',
                'name': 'wallet_name',
                'message': 'Enter wallet name:',
            },
            {
                'type': 'input',
                'name': 'wallet_key',
                'message': 'Enter wallet private key:',
            },
            {
                'type': 'list',
                'name': 'wallet_co',
                'message': 'Adding Wallet',
                'choices': ["Confirm", "Cancel"],
            }
        ]

        new_wallet = True    
        try:
            add_wallet_answers = prompt(add_wallet_questions, style=custom_style_2)
            new_wallet = Wallet(private_key=add_wallet_answers["wallet_key"], name=add_wallet_answers['wallet_name'])
        except(binascii.Error, TypeError):
            new_wallet = False

        finally:
            if(not new_wallet and add_wallet_answers["wallet_co"] == "Confirm"):
                os.system(console)
                print("\n  \033[31mPrivate Key is Wrong \n")
                main()
            elif(new_wallet and add_wallet_answers["wallet_co"] == "Confirm"):
                wallets.append(new_wallet)
                write_data(console)
                os.system('clear')
                print(" \033[32mWallet Stored.")
                main()
            else:
                os.system(console)
                main()

    def selected_wallet(wallet: Wallet):
        wallet_selected_questions = [
        {
            'type': 'list',
            'name': 'wallet_sq',
            'message': f"Wallet: {wallet.name}   --   {wallet.address}   --   {wallet.BNB_AMOUNT} BNB",
            'choices': ["Start Operation", "Remove Wallet", "<- BACK"],
        }
        ]
        answers1 = prompt(wallet_selected_questions, style=custom_style_2)
        if answers1['wallet_sq'] == '<- BACK':
           wallet_dashboard()
        elif answers1['wallet_sq'] == "Remove Wallet":
            wallets.remove(wallet)
            write_data(wallets)
            main()
        
        elif answers1['wallet_sq'] == "Start Operation":
            start_operation(wallet)
            time.sleep(5)
            print('\n\n\n')
            wallet_dashboard()

    def wallet_dashboard():
        if len(wallets) >= 1:
            try:
                def format_bnb_amount(amount):
                    return f"{amount:.5f}"
                wallet_dashboard_questions = [
                    {
                        'type': 'list',
                        'name': 'wallet_dashboard',
                        'message': '*',
                        'choices': [
                            {
                                'name': f"{wallet.name[:15]:<15} {wallet.address:<50} {format_bnb_amount(wallet.BNB_AMOUNT):<16}  {wallet.active:<7} {wallet.operation}",
                                'value': wallet.address  # Set the value to something unique for each choice
                            } for wallet in wallets
                        ] + ["<- BACK"]
                    },

                    ]
                print("\n   \33[33mName\t\t   Address\t\t\t\t\t       BNB\t      Active    Operation\033[0m")
                answers = prompt(wallet_dashboard_questions, style=custom_style_2)
                print('\n')
                if answers['wallet_dashboard'] == '<- BACK':
                    main()
                else:
                  
                    for wallet in wallets:
                        if wallet.address == answers['wallet_dashboard']:
                            selected_wallet(wallet)
                            break

            except KeyError:
                os.system('clear')
                print("\33[31mPlease Use Key arrow!")
                wallet_dashboard()
        else:
            print("\033[34mNo Wallets!\033[0m")
            main()
    
    
    answers = prompt(questions, style=custom_style_2)

    if answers.get("user_option") == "Wallets":
        os.system('clear')
        wallet_dashboard()

    elif answers.get("user_option") == "Add Wallet":
        store_wallet()

    elif answers.get("user_option") == "LOGS":
        log_array = read_log()
        for log in log_array: 
            print(log)
        main(None)
if __name__ == "__main__":
    main()


            