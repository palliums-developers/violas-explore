from violas_client import Client
from violas_client.libra_client.account import Account
from violas_client.move_core_types.language_storage import core_code_address
from db import get_latest_txs, get_send_txs, get_receive_txs, get_tx_header, get_txs_num, get_account_latest_txs, get_account_txs_num, get_send_num, get_receive_num, get_db_version

class ViolasClient():
    def __init__(self, url, faucet_file=None):
        self.client = Client.new(url, faucet_file)
        client.set_exchange_module_address(core_code_address())
        client.set_exchange_owner_address(association_address())
        self.swap_address=core_code_address().hex()
        self.url = url

    def get_latest_user_tx_headers(self, start, limit):
        return get_latest_txs(start, limit)

    def get_account_latest_tx_headers(self, address, start, limit):
        return get_account_latest_txs(address, start, limit)

    def get_user_tx_num(self):
        return get_txs_num()

    def get_account_tx_num(self, address):
        return get_account_txs_num(address)

    def get_send_tx_num(self, address):
        return get_send_num(address)

    def get_receive_tx_num(self, address):
        return get_receive_num(address)

    def get_latest_tx_headers(self, limit=10):
        version = self.client.get_latest_version()
        txs = self.client.get_transactions(version-limit, limit)
        return [get_tx_header(tx) for tx in reversed(txs)]

    def get_tx(self, version):
        return self.client.get_transaction(version)

    def get_account_state(self, address):
        return self.client.get_account_state(address)

    def get_latest_version(self):
        return self.client.get_latest_version()

    def get_transactions(self, start, limit, **kwargs):
        return self.client.get_transactions(start, limit, **kwargs)

    def get_transaction(self, version, **kwargs):
        return self.client.get_transaction(version, **kwargs)

    def get_balances(self, addr):
        return self.client.get_balances(addr)

    def get_send_txs(self, addr, start, limit):
        return get_send_txs(addr, start, limit)

    def get_received_txs(self, addr, start, limit):
        return get_receive_txs(addr, start, limit)

    def get_registered_currencies(self):
        return self.client.get_registered_currencies()

    def mint(self, addr, amount, currency_code, prefix_key):
        return self.client.mint_coin(addr, amount, auth_key_prefix=prefix_key, currency_code=currency_code)

    def get_liquidity_balances(self, addr):
        try:
            return self.client.swap_get_liquidity_balances(addr)
        except:
            return {}

    def get_swap_address(self):
        return self.swap_address

    def get_db_version(self):
        return get_db_version()

    def set_swap_address(self, address):
        self.swap_address = address
        self.client.set_exchange_module_address(address)

    def set_private_key(self, private_key):
        self.client.faucet_account = Account.faucet_account(bytes.fromhex(private_key))

    def set_url(self, url):
        url = bytes.fromhex(url).decode()
        self.url = url
        self.client.client.client.url = url


