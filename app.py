from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from chain import ViolasClient
from db import ViolasDB, get_tx_header
from werkzeug.routing import BaseConverter
import json


app = Flask(__name__)

client = ViolasClient("http://51.140.241.96:50001")


INDEX_SHOW_TX_NUM = 15

class AddressConvert(BaseConverter):
    def __init__(self,url_map,regex):
        super(AddressConvert, self).__init__(url_map)
        self.regex = regex

app.url_map.converters['re'] = AddressConvert


@app.errorhandler(Exception)
def handle_invalid_usage(e):
    import traceback
    return render_template("error.html", message=traceback.format_exc())

app.register_error_handler(400, handle_invalid_usage)


def shorthand(addr, sender=True):
    if addr is None or addr == "None":
        if sender:
            return "validator"
        else:
            return "n/a"
    return addr[:6] + "..." + addr[-6:]

def is_none(addr):
    return addr is None or addr == "None"

def handle_time(unix_timestamp):
    if unix_timestamp > 2**63:
        return "n/a"
    diff = datetime.now().timestamp() - unix_timestamp
    if diff >= 0:
        suffix = "ago"
    else:
        suffix = "later"
    diff = int(abs(diff))
    if diff == 0:
        return "just now"
    if diff < 60:
        return f"{diff}" + ' secs ' + f"{suffix}"

    if diff < 60*60:
        return f"{diff//60}" + ' mins ' + f"{diff%60}" + ' secs ' + f"{suffix}"
    diff = diff // 60
    if diff < 60*60:
        return f"{diff//60}" + ' hrs ' + f"{diff%60}" + ' mins ' + f"{suffix}"
    diff = diff // 60
    return f"{diff // 24}" + ' day ' + f"{diff % 24}" + ' hrs ' + f"{suffix}"

def time_format(timestamp):
    dt = datetime.fromtimestamp(timestamp+60*60*8)
    return str(dt)


@app.route("/swap/address/<re('[0-9a-fA-F]{32}'):addr>")
def set_swap_address(addr):
    client.set_swap_address(addr)
    return redirect(url_for("index"))

@app.route("/faucet/private_key/<re('[0-9a-fA-F]{64}'):private_key>")
def set_private_key(private_key):
    client.set_private_key(private_key)
    return redirect(url_for("index"))

@app.route("/url/<url>")
def set_url(url):
    client.set_url(url)
    return redirect(url_for("index"))

@app.route("/")
def index():
    headers = client.get_latest_user_tx_headers(0, INDEX_SHOW_TX_NUM)
    latest_version = client.get_latest_version()
    total_num = client.get_user_tx_num()
    start_time = client.get_transaction(2).get_expiration_time()
    swap_address = client.get_swap_address()
    db_version = client.get_db_version()
    return render_template("index.html", headers=headers, latest_version=latest_version, handle_time=handle_time,
                           shorthand=shorthand, time_format=time_format, sender=None, is_none=is_none,
                           total_num=total_num, start_time=start_time, swap_address=swap_address, db_version=db_version)

@app.route("/address/<re('[0-9a-fA-F]{32}'):addr>")
def account_state(addr):
    page = int(request.args.get("p", 1))
    start = INDEX_SHOW_TX_NUM * (page-1)
    account = client.get_account_state(addr)
    libra_balance = account.get_balance("LBR")
    if libra_balance is None:
        libra_balance = 0
    balances = client.get_balances(addr)
    balances = json.dumps(balances, indent=2)
    headers = client.get_account_latest_tx_headers(addr, start, INDEX_SHOW_TX_NUM)
    total_num = client.get_account_tx_num(addr)
    send_num = client.get_send_tx_num(addr)
    received_num = client.get_receive_tx_num(addr)
    liquidity_balances = client.get_liquidity_balances(addr)
    liquidity_balances = json.dumps(liquidity_balances, indent=2)

    return render_template("account.html", account = account, headers=headers, balances=balances,
                           libra_balance=libra_balance, handle_time=handle_time, shorthand=shorthand,
                           time_format=time_format, sender=addr, is_none=is_none, send_num=send_num, received_num=received_num,
                           total_num=total_num, liquidity_balances=liquidity_balances)

@app.route("/transactions")
def txs():
    page = int(request.args.get("p", 1))
    start = INDEX_SHOW_TX_NUM * (page-1)
    addr = request.args.get("q")
    flag = int(request.args.get("f", "0"))
    total_num, headers = 0, []
    if addr is None:
        headers = client.get_latest_user_tx_headers(start, INDEX_SHOW_TX_NUM)
        total_num = client.get_user_tx_num()
    else:
        if flag == 0:
            headers = client.get_account_latest_tx_headers(addr, start, INDEX_SHOW_TX_NUM)
            total_num = client.get_account_tx_num(addr)
        if flag == 1:
            headers = client.get_send_txs(addr, start, INDEX_SHOW_TX_NUM)
            total_num = client.get_send_tx_num(addr)
        if flag == 2:
            headers = client.get_received_txs(addr, start, INDEX_SHOW_TX_NUM)
            total_num = client.get_receive_tx_num(addr)


    total_page = total_num // INDEX_SHOW_TX_NUM
    if total_num % INDEX_SHOW_TX_NUM:
        total_page += 1

    return render_template("txs.html", headers=headers, total_num=total_num, total_page=total_page, cur_page=page, handle_time=handle_time, shorthand=shorthand, sender=addr, is_none=is_none)

@app.route("/version/<int:version>")
def tx(version):
    tx = client.get_transaction(version)
    tx_header = get_tx_header(tx)
    tx_header["tx"] = tx
    return render_template("tx.html", tx=tx_header, handle_time=handle_time, time_format=time_format)

@app.route("/search")
def search():
    addr_or_version = request.args.get("q")
    if len(addr_or_version) == 0:
        return redirect(url_for("index"))
    if len(addr_or_version) == 32:
        return redirect(url_for("account_state", addr=addr_or_version))
    return redirect(url_for("tx", version=addr_or_version))

@app.route("/faucet", methods=["GET", "POST"])
def faucet():
    if request.method == "POST":
        authentication_key = request.form["ctl00$ContentPlaceHolder1$txtAddress"]
        address = authentication_key[-32:]
        prefix_key = authentication_key[:32]
        amount = int(request.form["ctl00$ContentPlaceHolder1$txtAmount"])*(10**6)
        currency_code = request.form["ctl00$ContentPlaceHolder1$txtCurrency"]
        client.mint(address, amount, currency_code, prefix_key)
    registered_currencies = client.get_registered_currencies()

    return render_template("faucet.html", registered_currencies=registered_currencies)


if __name__ == "__main__":
    t = ViolasDB(client)
    t.start()
    app.run(host="0.0.0.0", port=8000, debug=False)

