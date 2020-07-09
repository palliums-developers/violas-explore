import time
import sqlite3
from threading import Thread

from violas_client.extypes.view import TransactionView
from violas_client.lbrtypes.bytecode import CodeType
from violas_client.extypes.bytecode import CodeType as ExchangeType


db_version = 1703000
def get_db_version():
    return db_version

def get_tx_header(tx):
    code_type = tx.get_code_type()
    if code_type == ExchangeType.ADD_LIQUIDITY:
        event = tx.get_swap_event()
        currency_code = f"{event.coina}--{event.coinb}"
        amount = f"{event.deposit_amounta}--{event.deposit_amountb}"
    elif code_type == ExchangeType.REMOVE_LIQUIDITY:
        event = tx.get_swap_event()
        currency_code = f"{event.coina}--{event.coinb}"
        amount = f"{event.withdraw_amounta}--{event.withdraw_amountb}"
    elif code_type == ExchangeType.SWAP:
        event = tx.get_swap_event()
        currency_code = f"{event.input_name}--{event.output_name}"
        amount = f"{event.input_amount}-->{event.output_amount}"
    else:
        currency_code = tx.get_currency_code()
        amount = str(tx.get_amount())

    if currency_code is None:
        currency_code = "LBR"
    if amount is None:
        amount = 0
    gas_currency = tx.get_gas_currency()
    if gas_currency is None:
        gas_currency = "LBR"
    if tx.is_successful():
        state = "success"
    else:
        state = "fail"
    header = {
        "version": tx.get_version(),
        "ex_time": tx.get_expiration_time(),
        "code_type": tx.get_code_type().name.lower(),
        "sender": tx.get_sender(),
        "receiver": tx.get_receiver(),
        "amount": amount,
        "currency_code": currency_code,
        "gas_used": 0,
        "gas_currency": gas_currency,
        "state": state
    }
    return header

def create_violas_table():
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    try:
        cursor.execute(f"drop table violas")
    except:
        pass
    sql = f"create table violas (version int primary key, expiration_time int, type varchar(32), sender varchar(32), receiver varchar(32), amount varchar(100) , currency_code, gas_fee int, gas_currency varchar ,  success varchar)"
    cursor.execute(sql)
    sql = "create index sender on violas (sender)"
    cursor.execute(sql)
    sql = "create index receiver on violas (receiver)"
    cursor.execute(sql)


def insert_transaction(tx: TransactionView):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    header = list(get_tx_header(tx).values())
    sql = f"insert into violas values ({header[0]},{header[1]},'{header[2]}','{header[3]}','{header[4]}','{header[5]}','{header[6]}','{header[7]}','{header[8]}','{header[9]}')"
    cursor.execute(sql)
    conn.commit()

def insert_transactions(txs: TransactionView):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    for tx in txs:
        header = list(get_tx_header(tx).values())
        sql = f"insert into violas values ({header[0]},{header[1]},'{header[2]}','{header[3]}','{header[4]}','{header[5]}','{header[6]}','{header[7]}','{header[8]}','{header[9]}')"
        cursor.execute(sql)
    conn.commit()

def get_latest_txs(start, limit):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = f"select * from violas order by version desc limit {limit} offset {start}"
    values = cursor.execute(sql)
    return values.fetchall()

def get_txs_num():
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = "select count(*) from violas"
    values = cursor.execute(sql)
    return values.fetchall()[0][0]

def get_send_num(addr):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = f"select count(*) from violas where sender='{addr}'"
    values = cursor.execute(sql)
    return values.fetchall()[0][0]

def get_receive_num(addr):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = f"select count(*) from violas where receiver='{addr}'"
    values = cursor.execute(sql)
    return values.fetchall()[0][0]

def get_account_txs_num(addr):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = f"select count(*) from violas where sender='{addr}' or receiver='{addr}' "
    values = cursor.execute(sql)
    return values.fetchall()[0][0]


def get_account_latest_txs(addr, start, limit):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = f"select * from violas where sender='{addr}' or receiver='{addr}'  order by version desc limit {limit} offset {start}"
    values = cursor.execute(sql)
    return values.fetchall()

def get_send_txs(sender_address, start, limit):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = f"select * from violas where sender='{sender_address}'  order by version desc limit {limit} offset {start}"
    values = cursor.execute(sql)
    return values.fetchall()

def get_receive_txs(receiver_address, start, limit):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    sql = f"select * from violas where receiver='{receiver_address}' order by version desc limit {limit} offset {start}"
    values = cursor.execute(sql)
    return values.fetchall()

class ViolasDB(Thread):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        global db_version
        create_violas_table()
        limit = 500
        while True:
            try:
                user_txs = []
                txs = self.client.get_transactions(db_version, limit)
                if len(txs) == 0:
                    time.sleep(1)
                    continue
                for tx in txs:
                    if tx.get_code_type() not in (CodeType.BLOCK_METADATA, CodeType.CHANGE_SET):
                        user_txs.append(tx)
                insert_transactions(user_txs)
                db_version += len(txs)
            except Exception as e:
                print(e)

#

if __name__ == "__main__":
    print(get_send_num("6c2920f1c3c08bcbb6e5a8f090a1dde0"))

