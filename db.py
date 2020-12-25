import time
import sqlite3
from threading import Thread

from violas_client.extypes.view import TransactionView
from violas_client.lbrtypes.bytecode import CodeType
from violas_client.extypes.bytecode import CodeType as ExchangeType


db_version = 0

def get_db_version():
    return db_version

def get_tx_header(tx):
    code_type = tx.get_code_type()
    if code_type == ExchangeType.ADD_LIQUIDITY and tx.is_successful():
        event = tx.get_swap_type_events(code_type)[0].get_swap_event()
        amount = f"{event.deposit_amounta/10**6}{event.coina}--{event.deposit_amountb/10**6}{event.coinb}"
    elif code_type == ExchangeType.REMOVE_LIQUIDITY and tx.is_successful():
        event = tx.get_swap_type_events(code_type)[0].get_swap_event()
        amount = f"{event.withdraw_amounta/10**6}{event.coina}--{event.withdraw_amountb/10**6}{event.coinb}"
    elif code_type == ExchangeType.SWAP and tx.is_successful():
        event = tx.get_swap_type_events(code_type)[0].get_swap_event()
        amount = f"{event.input_amount/10**6}{event.input_name}->{event.output_amount/10**6}{event.output_name}"
    else:
        currency_code = tx.get_currency_code()
        if currency_code is None:
            currency_code = "LBR"
        amount = tx.get_amount()
        if amount is None:
            amount = 0
        amount = f"{amount/10**6} {currency_code}"

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
        "gas_used": tx.get_gas_used_price(),
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
    sql = f"create table violas (version int primary key, expiration_time int, type varchar(32), sender varchar(32), receiver varchar(32), amount varchar(100) , gas_fee int, gas_currency varchar ,  success varchar)"
    cursor.execute(sql)
    sql = "create index sender on violas (sender)"
    cursor.execute(sql)
    sql = "create index receiver on violas (receiver)"
    cursor.execute(sql)


def insert_transaction(tx: TransactionView):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    header = list(get_tx_header(tx).values())
    sql = f"insert into violas values ({header[0]},{header[1]},'{header[2]}','{header[3]}','{header[4]}','{header[5]}',{header[6]},'{header[7]}','{header[8]}')"
    cursor.execute(sql)
    conn.commit()

def insert_transactions(txs: TransactionView):
    conn = sqlite3.connect('txs.db')
    cursor = conn.cursor()
    for tx in txs:
        header = list(get_tx_header(tx).values())
        sql = f"insert into violas values ({header[0]},{header[1]},'{header[2]}','{header[3]}','{header[4]}','{header[5]}',{header[6]},'{header[7]}','{header[8]}')"
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
            # try:
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
            # except Exception as e:
            #     print(e)

#

if __name__ == "__main__":
    print(get_send_num("6c2920f1c3c08bcbb6e5a8f090a1dde0"))

