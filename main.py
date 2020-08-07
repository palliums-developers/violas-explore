# from enum import IntEnum
# url = b"1"
# print(url.decode())
from libra_client import Client

client = Client("bj_testnet")
print(client.faucet_account.private_key)


