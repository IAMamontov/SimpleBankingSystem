# Write your code here
import secrets
import sqlite3
from sqlite3.dbapi2 import Cursor

menu_top = "\
1. Create an account\n\
2. Log into account\n\
0. Exit"
menu_logged = "\
1. Balance\n\
2. Add income\n\
3. Do transfer\n\
4. Close account\n\
5. Log out\n\
0. Exit"

accounts = []


def luhn_sum(str_number):
    s = 0
    for i in range(0, len(str_number), 2):
        # print(str_number[i], end=" ")
        digit = int(str_number[i]) * 2
        if digit > 9:
            digit = digit - 9
        s = s + digit
    for i in range(1, len(str_number), 2):
        s = s + int(str_number[i])
    # print(s)
    return s


class Account:

    def __init__(self):
        self.prefix = "400000"
        self.id = 0
        self.card_number = ""
        self.pin = ""
        self.balance = 0

    def create_new(self, account_number):
        self.id = account_number
        self.pin = "{:04d}".format(secrets.randbelow(10000))
        self.balance = 0
        self.card_number = self.prefix + "{:09d}".format(self.id)
        if luhn_sum(self.card_number) % 10 > 0:
            checksum = 10 - (luhn_sum(self.card_number) % 10)
        else:
            checksum = 0
        self.card_number = self.card_number + str(checksum)

    def create_from_db(self, new_id, card_number, pin, balance):
        self.id = new_id
        self.card_number = card_number
        self.pin = pin
        self.balance = balance


def read_from_db():
    cur.execute("SELECT * FROM card")
    answer = cur.fetchone()
    while answer is not None:
        new_id = answer[0]
        card_number = answer[1]
        pin = answer[2]
        balance = answer[3]
        new_account = Account()
        new_account.create_from_db(new_id, card_number, pin, balance)
        accounts.append(new_account)
        answer = cur.fetchone()


def create():
    new_id = len(accounts)
    for _ in accounts:
        if _.id == new_id:
            new_id = new_id + 1
    new_account = Account()
    new_account.create_new(new_id)
    cur.execute("INSERT INTO card(id, number, pin, balance) "
                "VALUES (:id, :number, :pin, :balance);",
                {"id": new_account.id, "number": new_account.card_number,
                 "pin": new_account.pin, "balance": new_account.balance})
    conn.commit()
    print("\
Your card has been created\n\
Your card number:")
    # print("{}{:010d}".format(new_account.prefix, new_account.number))
    print(new_account.card_number)
    print("Your card PIN:")
    print(new_account.pin)
    return new_account


def login():
    print("Enter your card number:")
    card_number = input(">")
    print("Enter your PIN:")
    pin = input(">")
    for _ in accounts:
        if card_number == _.card_number \
                and pin == _.pin:
            print("You have successfully logged in!")
            logged_loop(_)
    print("Wrong card number or PIN!")
    main_loop()


def log_out():
    print("You have successfully logged out!")


def show_balance(account):
    print("Balance {}".format(account.balance))


def add_income(account):
    print("Enter income:")
    income = int(input(">"))
    account.balance = account.balance + income
    cur.execute("UPDATE card SET balance = :new_balance "
                "WHERE id = :id;", {"new_balance": account.balance, "id": account.id})
    conn.commit()
    print("Income was added!")


def do_transfer(account):
    print("Transfer")
    print("Enter card number:")
    target_card_number = input(">")
    if target_card_number == account.card_number:
        print("You can't transfer money to the same account!")
        return
    numb15 = target_card_number[:15]
    if luhn_sum(numb15) % 10 > 0:
        checksum = 10 - (luhn_sum(numb15) % 10)
    else:
        checksum = 0
    if int(target_card_number[-1:]) != checksum:
        print("Probably you made a mistake in the card number. Please try again!")
        return
    for _ in accounts:
        if target_card_number == _.card_number:
            print("Enter how much money you want to transfer:")
            transfer = int(input(">"))
            if transfer > account.balance:
                print("Not enough money!")
                return
            else:
                account.balance = account.balance - transfer
                _.balance = _.balance + transfer
                cur.execute("UPDATE card SET balance = :new_balance "
                            "WHERE id = :id;", {"new_balance": account.balance, "id": account.id})
                conn.commit()
                cur.execute("UPDATE card SET balance = :new_balance "
                            "WHERE id = :id;", {"new_balance": _.balance, "id": _.id})
                conn.commit()
                print("Success!")
                return
    print("Such a card does not exist.")


def close_account(account):
    cur.execute("DELETE FROM card WHERE id = :id ", {"id": account.id})
    conn.commit()
    accounts.remove(account)
    print("The account has been closed!")


def exit_():
    cur.close()
    conn.close()
    print("Bye!")
    exit()


def main_loop():
    while True:
        print(menu_top)
        choice = int(input(">"))
        if choice == 1:
            accounts.append(create())
            # for _ in accounts:
            #     print("{}{:010d} {:04d} {}".format(_.prefix, _.number, _.pin, _.balance))
            continue
        elif choice == 2:
            login()
            continue
        elif choice == 0:
            exit_()
            break
        else:
            continue


def logged_loop(account):
    while True:
        print(menu_logged)
        choice = int(input(">"))
        if choice == 1:
            show_balance(account)
        elif choice == 2:
            add_income(account)
        elif choice == 3:
            do_transfer(account)
        elif choice == 4:
            close_account(account)
            main_loop()
            break
        elif choice == 5:
            log_out()
            main_loop()
            break
        elif choice == 0:
            exit_()
            break
        else:
            continue


conn = sqlite3.connect("card.s3db")
cur: Cursor = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS card("
            "id INTEGER, number TEXT, pin TEXT, balance INTEGER DEFAULT 0);")
conn.commit()

read_from_db()

main_loop()
