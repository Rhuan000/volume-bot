from web3 import Web3
from token_abi import TOKEN_ABI
from eth_account import Account

web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545/"))
#https://bsc-dataseed.binance.org/
class Wallet:
    def __init__(self, private_key: str, name: str):
        self.name = name
        self.private_key = private_key
        self.address = web3.to_checksum_address(self.get_address())
        self.BNB_AMOUNT = self.get_bnb_amount()
        self.nonce = web3.eth.get_transaction_count(self.address) 
        self.tokens = {}
        self.active = False
        self.operation = None
        self.previous_operation = ''

    def get_address(self):
        PA = Account.from_key(self.private_key)
        return PA.address
    
    def get_bnb_amount(self) -> float: 
        balance_wei = web3.eth.get_balance(self.address)
        balance_bnb = web3.from_wei(balance_wei, 'ether')
        self.BNB_AMOUNT = balance_bnb
        return balance_bnb
    

    def get_token_amount(self, token_address) -> float:
        token_contract = web3.eth.contract(address=token_address, abi=TOKEN_ABI)
        token_balance = token_contract.functions.balanceOf(self.address).call()
        return token_balance
    
    def change_active(self) -> None:
        if self.status == True:
            self.status = False
        else:
            self.status = True

    def set_operation(self, operation: str) -> None:
        self.operation = operation
    
    def add_token_balance(self, address: str, symbol: str, balance: int):
        balance = web3.from_wei(balance, "ether")
        self.tokens[address] = {
            'symbol': symbol,
            'balance': balance
        }
        