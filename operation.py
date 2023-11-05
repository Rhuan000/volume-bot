from wallet import Wallet, web3
from token_abi import SWAPV3_ADDRESS, SWAPV3_ABI, TOKEN_ABI, SWAPV2_ADDRESS, SWAPV2_ABI, PAYC_PROXY_ABI
import threading
import datetime
from data import write_data
import time
import math
import uuid

class Operation:
    def __init__(self, wallet: Wallet, token_address: str, price_buy: float, price_sell: float,wbnb_amount: float):
        '''"price_buy" and "price_sell" and "amount" on BNB.'''
        
        if price_buy >= price_sell:
            raise Exception(f"Price Buy Can't be equal to or higher than Sell! {price_buy}, {price_sell}")
        self.id = str(uuid.uuid4()) 
        self.wallets: [Wallet] =  []
        self.token_target = web3.to_checksum_address(token_address)
        self.WBNB = web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
        self.token_contract = web3.eth.contract(address=self.token_target, abi=TOKEN_ABI)
        self.token_symbol = self.get_token_symbol()
        self.wbnb_amount = wbnb_amount
        self.token_amount = 0
        self.price_buy = price_buy
        self.price_sell = price_sell
        self.active = False
        self.previous = ''
        self.buy_flag = threading.Event()
        self.sell_flag = threading.Event()
        self.add_wallet(wallet)

    

    def start(self):
            self.active = True
            for wallet in self.wallets:
                wallet.active = True
            def trigger_flag():
                while(self.active):
                    token_price =  self.get_token_actual_price()
                    if(token_price <= self.price_buy):
                        self.buy_flag.set()
                             
                    elif(token_price >= self.price_sell and (self.previous == 'buy' or self.previous == '')):
                        self.sell_flag.set()
                        
                
            self.active = True
            self.log(f"\033[33m*** Operation Started with \033[35m{len(self.wallets)}\033[33m Wallets ***\033[0m\n")
            print(f"\033[33m*** Operation Started with \033[35m{len(self.wallets)}\033[33m Wallets ***\033[0m\n")
            threading.Thread(target=trigger_flag).start()
            
        
    def operate_with_flag(self, wallet: Wallet):
                while(wallet.active):
                    if(self.buy_flag.is_set() == True and (wallet.previous_operation == 'sell' or wallet.previous_operation == '')):
                        self.buy(wallet)
                        self.previous = 'buy'
                        wallet.previous_operation = 'buy'
                        self.buy_flag.clear()
                    if(self.sell_flag.is_set() == True and (wallet.previous_operation == 'buy' or wallet.previous_operation == '')):
                        self.sell(wallet)
                        self.previous = 'sell'
                        wallet.previous_operation = 'sell'
                        self.sell_flag.clear()
             

    def stop(self):
        self.active = False
        for wallet in self.wallets:
            wallet.active = False
            wallet.operation = None
            time.sleep(1)
            wallet.previous_operation = ''

    def get_token_actual_price(self):
        token_decimals = self.token_contract.functions.decimals().call()
        tokens_to_sell = int(str(1).ljust(token_decimals + len(str(1)), '0'))

        SWAPV2_CONTRACT = web3.eth.contract(address=SWAPV2_ADDRESS, abi=SWAPV2_ABI)
        amountOut = SWAPV2_CONTRACT.functions.getAmountsOut(tokens_to_sell, [self.token_target, self.WBNB]).call()
        amountOut = web3.from_wei(amountOut[1], 'ether')
        self.token_price = float(amountOut)
        return self.token_price

    def remove_wallet(self, wallet: Wallet):
        wallet.active = False
        wallet.operation = None
        time.sleep(1)
        wallet.previous_operation = ''
        self.wallets.remove(wallet)
        self.log(f'Wallet: {wallet.name} -- {wallet.address} Removed From operation!')

    def add_wallet(self, wallet: Wallet):
        if wallet not in self.wallets:
            self.wallets.append(wallet)
            wallet.operation = self.id
            wallet.active = True
            if self.previous == 'buy':
                self.buy(wallet)
                wallet.previous_operation = 'buy'

            threading.Thread(target=self.operate_with_flag, args=(wallet,)).start()
            self.log(f'\033[32m\nWallet Added\nOperation Active: \033[35m{self.active}! \033[32mhas \033[35m{len(self.wallets)} \033[32m\nWallets.\033[0m\n{wallet.name} -- {wallet.address}\n\033[0m')
        else:
            self.log(f"\033[91m\nWallet Already in this Operation.\033[0m -- {wallet.address}")
            raise Exception(f"\033[31mError with: {wallet.name} -- {wallet.address} -- \033[33m\nWallet Already in Operation!\033[0m\n")
    
    def change_wbnb_amount(self, new_value: float):
        self.wbnb_amount = new_value

    def change_token_amount(self, new_value: float):
        self.token_amount = new_value
    
    def get_token_symbol(self) -> str:
        symbol = self.token_contract.functions.symbol().call()
        return symbol

    def get_token_balance(self, wallet: Wallet) -> str:      
        balance = self.token_contract.functions.balanceOf(wallet.address).call()
        wallet.add_token_balance(self.token_target, self.token_symbol, balance)
        return balance
    
    def buy(self, wallet: Wallet, value=None) -> str:
        try:
            nonce = web3.eth.get_transaction_count(wallet.address, 'latest')
            if value == None:
                value = self.wbnb_amount
            contract = web3.eth.contract(address=SWAPV3_ADDRESS, abi=SWAPV3_ABI)
            pancakeswap3_txn = contract.functions.exactInputSingle({
                'tokenIn': self.WBNB,
                'tokenOut': self.token_target,  
                'fee': 10000,
                'recipient': wallet.address,
                'deadline': (int(time.time() + 10000)),
                'amountIn': web3.to_wei(value, 'ether'),
                'amountOutMinimum': 0,
                'sqrtPriceLimitX96': 0
                }).build_transaction({
                    'value': web3.to_wei(value, 'ether'),
                    'gas': 1500000,
                    'gasPrice': web3.to_wei(5, 'gwei'),
                    'nonce': nonce,
                    'chainId': 56,
                })
            
            signed_transaction = web3.eth.account.sign_transaction(pancakeswap3_txn, wallet.private_key)
            # Send the transaction
            
            tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)

            # Wait for the transaction to be confirmed
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            wallet.get_bnb_amount()
            if receipt['status'] == 1:
                self.log(f"\033[32mTransaction Success! (Bought)\033[0m\nWallet: {wallet.name} -- {wallet.address}\nTransaction Hash: {receipt.transactionHash.hex()}\n")
                
                return receipt
            else:
                raise Exception(f"\033[91mTransaction Failed! (Buy)(\033[0m\n{receipt}\n")
            
        except Exception as e:
            if 'nonce' in str(e) or '-32003' in str(e) and wallet.retry == 0:
                # Handle nonce-related error
                self.log(f"\033[31mNonce-related error: Retrying\033[0m\nWallet: {wallet.name} --- {wallet.address}\n")
                time.sleep(7)
                self.buy(wallet, 0.000001)
                wallet.retry = 1
            else:
                # Handle other types of errors
                index = self.wallets.index(wallet)
                self.wallets.pop(index)
                wallet.active = False
                wallet.operation = None
                time.sleep(1)
                wallet.previous_operation = ''
                self.log(f"\033[31mError with: {wallet.name} -- {wallet.address} -- \033[33m\nWallet removed from Operation!\033[0m\n{e}\n")

    def sell(self, wallet: Wallet):
        try:
            value = self.token_amount
            contract = web3.eth.contract(address=SWAPV3_ADDRESS, abi=SWAPV3_ABI)
            token_contract = web3.eth.contract(address=self.token_target, abi=TOKEN_ABI)

            # Check token balance
            balance = token_contract.functions.balanceOf(wallet.address).call()
            if balance <= 0:
                raise Exception("\033[31mInsufficient balance to perform the swap.\033[0m\nnWallet: {wallet.name} -- {wallet.address} ")
            
            # Approve PancakeSwap to spend a specific amount
            approval_amount = balance  # You can specify a different amount if needed
            approve_txn = token_contract.functions.approve(SWAPV3_ADDRESS, approval_amount).build_transaction({
                'from': wallet.address,
                'gasPrice': web3.to_wei(5, 'gwei'),
                'nonce': web3.eth.get_transaction_count(wallet.address, 'latest'),
                'chainId': 56,
                'gas': 200000,  # Adjust the gas limit as needed
            })
            signed_approve_txn = web3.eth.account.sign_transaction(approve_txn, private_key=wallet.private_key)
            
            # Send the approval transaction
            approve_tx_hash = web3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)

            # Wait for approval transaction receipt
            approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)

            if approve_receipt['status'] != 1:
                raise Exception(f"\033[91mApproval Transaction Failed! (Approval)\033[0m\n{approve_receipt}")
            else:
                self.log(f"\033[32mTransaction Success! \033[34m(Approval)\033[0m\nWallet: {wallet.name} -- {wallet.address} -- Transaction Hash: {approve_receipt.transactionHash.hex()}\n")
            
            # Proceed with the swap
            path = [self.WBNB, self.token_target]
            deadline = (int(time.time()) + 10000)
            swap_txn = contract.functions.exactInputSingle({
                'tokenIn': path[1],
                'tokenOut': path[0],
                'fee': 10000,
                'recipient': wallet.address,
                'deadline': deadline,
                'amountIn': balance,  
                'amountOutMinimum': 0,
                'sqrtPriceLimitX96': 0
            }).build_transaction({
                #'value': balance,
                'from': wallet.address,
                'gas': 1500000,
                'gasPrice': web3.to_wei(5, 'gwei'),
                'nonce': web3.eth.get_transaction_count(wallet.address, 'latest'),
                'chainId': 56,
            })

            signed_swap_txn = web3.eth.account.sign_transaction(swap_txn, private_key=wallet.private_key)
            
            # Send the swap transaction
            swap_tx_hash = web3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)

            # Wait for the swap transaction receipt
            swap_receipt = web3.eth.wait_for_transaction_receipt(swap_tx_hash)

            if swap_receipt['status'] == 1:
                self.log(f"\033[32mTransaction Success! \033[91m(Sold)\033[0m\nWallet: {wallet.name} -- {wallet.address} -- Transaction Hash: {swap_receipt.transactionHash.hex()}\n")
                self.log(swap_receipt.transactionHash.hex()+'\n')
                return swap_receipt
            else:
                raise Exception(f"\033[91mTransaction Failed! (Sell)\033[0m\nOperation: {self.id}{swap_receipt}\n")
            
        except Exception as e:
            index = self.wallets.index(wallet)
            self.wallets.pop(index)
            wallet.active = False
            self.log(f"\033[31mError with: {wallet.name} -- {wallet.address} -- \033[33m\nWallet removed from Operation!\033[0m\n{e}\n ")
        wallet.get_bnb_amount()
        
    def log(self, message):
        # Esta função registra a mensagem no arquivo de log
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"Operation: {self.id} - {timestamp} - {message}\n"
        with open("log.txt", "a") as log_file:
            log_file.write(log_message)
