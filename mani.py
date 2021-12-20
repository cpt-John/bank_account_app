# pip install dnspython
# pip install pymongo[srv]
# pip install colorama

import os
from pymongo import MongoClient
import re


class Fore:
    LIGHTGREEN_EX = ''
    LIGHTBLUE_EX = ''
    GREEN = ''
    RED = ''
    YELLOW = ''
    CYAN = ''


class Style:
    RESET_ALL = ''


try:
    from colorama import Fore, Style
    pass
except:
    print("colorama import failed")


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    return False


DB_COLLECTION = ''
FIELDS = {'Name': 'Name', 'Ph_number': 'Ph_number', 'Email': 'Email',
          'Pan': 'Pan', 'Aadhar': 'Aadhar', 'Balance': 'Balance', 'Account_number': 'Account_number'}
ACCOUNT_NUMBER = ''  # emulate redis token


def db_init():
    fileName = "db_link.txt"
    db_link = ''
    try:
        file = open(fileName, "r")
        db_link = file.read()
        file.close()
    except:
        pass
    link_exists = bool(db_link)
    if not link_exists:
        db_link = input("enter mongodb connection url: ")
        file = open(fileName, "w")
        file.write(db_link)
        file.close()
    client = ''
    try:
        client = MongoClient(db_link)
        db = client.bank_app
        return db.bank_doc
    except Exception as e:
        print("db connection failed")
        raise Exception(e)


def db_operation(db_collection, operation='r', condition={}, data={}, fields={}):
    try:
        switch = {
            'c': lambda: db_collection.count_documents(condition),
            'r': lambda: db_collection.find(condition, fields).sort(FIELDS["Name"]),
            'r_o': lambda: db_collection.find_one(condition, fields),
            'w': lambda: db_collection.insert_one(data),
            'u': lambda: db_collection.update_one(condition, data),
            'd': lambda: db_collection.delete_one(condition)
        }
        response = switch[operation]()
        return response
    except Exception as e:
        switch = {
            'c': 0,
            'r': {},
            'r_o': {},
            'w': {},
            'u': False,
            'd': False,
        }
        print("Error during:", operation, e)
        return switch[operation]


def pretty_print_statement(string, line='.', length=6, color=''):
    print(f"\n{color}{line*length}{string}{line*length}\n{Style.RESET_ALL}")


def pretty_print_dict(dict):
    string = '-'*25+'\n'
    for key in list(dict.keys()):
        spaces = max(14 - len(key), 1)
        string += f"{key}{' '*spaces}: {dict[key]}\n"
    string += '='*25
    print(f'{Fore.LIGHTBLUE_EX}{string}{Style.RESET_ALL}')


def regex_validate(type, test_string):
    switch = {
        "Name": re.compile(r"^[A-Za-z]{3,15}\d{0,5}$"),
        "Ph_number": re.compile(r"^\+?[0-9]{6,12}$"),
        "Email": re.compile(r"^\w{3,7}@\w{3,10}.\w{1,5}$"),
        "Pan": re.compile(r"^\w{10}$"),
        "Aadhar": re.compile(r"^\d{12}$"),
        "Amount": re.compile(r"^\d{1,7}$")
    }
    return bool(re.fullmatch(switch[type], test_string))


def validate(validate_func, function_args):
    return bool(validate_func(*function_args))


def create():
    name = input("enter name: ").strip()
    ph_number = input("enter ph.number: ").strip()
    email = input("enter email: ").strip()
    pan = input("enter pan(10-digit): ").strip()
    aaadhar = input("enter aaadhar(12-digit): ").strip()
    field_args = [[FIELDS["Name"], name], [FIELDS["Ph_number"], ph_number], [
        FIELDS["Email"], email], [FIELDS["Pan"], pan], [FIELDS["Aadhar"], aaadhar]]
    regex_validation_result = [
        validate(regex_validate, args) for args in field_args]
    if len(regex_validation_result) != sum(regex_validation_result):
        error_field = field_args[regex_validation_result.index(False)][0]
        pretty_print_statement(f"{error_field} is invalid", color=Fore.RED)
        return False
    duplicate_validation_result = [
        validate(
            lambda arg1, arg2:
                db_operation(DB_COLLECTION, operation='c', condition={arg1: arg2}) < 1, args)
        for args in field_args]
    if len(duplicate_validation_result) != sum(duplicate_validation_result):
        error_field = field_args[duplicate_validation_result.index(False)][0]
        pretty_print_statement(f"{error_field} is duplicate", color=Fore.RED)
        return False
    selected = input("Confirm details?(y/n): ").strip().lower()
    if selected == 'y':
        customer = {field[0]: field[1] for field in field_args}
        customer[FIELDS['Account_number']] = f'{aaadhar[-4:]}{pan[-4:]}'
        customer[FIELDS['Balance']] = 0
        db_operation(DB_COLLECTION, 'w', data=dict(customer))
        pretty_print_statement("Saved!",
                               color=Fore.LIGHTGREEN_EX)
        pretty_print_dict(customer)
        return True
    return False


def login():
    account_number = input("enter account number(8-digit): ")
    login_arguments = [FIELDS["Account_number"], account_number]
    exists = validate(lambda arg1, arg2:
                      db_operation(DB_COLLECTION, operation='c', condition={arg1: arg2}) > 0, login_arguments)
    if exists:
        global ACCOUNT_NUMBER
        ACCOUNT_NUMBER = account_number
        return True
    pretty_print_statement("Account doest exist!", color=Fore.RED)
    return False


def logout():
    global ACCOUNT_NUMBER
    ACCOUNT_NUMBER = ''
    pretty_print_statement("Logged out!",
                           color=Fore.LIGHTYELLOW_EX)
    return True


def account_details_helper(fields=[]):
    view_fields = {field: 1 for field in FIELDS}
    view_fields["_id"] = 0
    details = db_operation(
        DB_COLLECTION, operation='r_o', condition={FIELDS['Account_number']: ACCOUNT_NUMBER}, fields=view_fields)
    filtered_details = {field: details[field]
                        for field in fields} if len(fields) else details
    return filtered_details


def statement():
    statement_ = account_details_helper(
        [FIELDS['Account_number'], FIELDS['Balance']])
    statement_[FIELDS['Balance']] = f"${statement_[FIELDS['Balance']]}"
    pretty_print_dict(statement_)
    return True


def deposit():
    deposit_amount = input("enter amount(min 1): ")
    if not validate(regex_validate, ["Amount", deposit_amount]):
        pretty_print_statement("Invalid Aomunt!", Fore.RED)
        return False
    deposit_amount = int(deposit_amount)
    if deposit_amount < 1:
        pretty_print_statement("Amount Must be min 1!", Fore.RED)
        return False
    balance = int(account_details_helper()[FIELDS['Balance']])
    new_balance = balance+deposit_amount
    update_query = {"$set": {FIELDS['Balance']: new_balance}}
    db_operation(
        DB_COLLECTION, operation='u', condition={FIELDS["Account_number"]: ACCOUNT_NUMBER}, data=update_query)
    pretty_print_statement("Deposit success!", color=Fore.GREEN)
    statement()
    return True


def withdraw():
    withdraw_amount = input("enter amount(min 1): ")
    if not validate(regex_validate, ["Amount", withdraw_amount]):
        pretty_print_statement("Invalid Aomunt!", Fore.RED)
        return False
    withdraw_amount = int(withdraw_amount)
    balance = int(account_details_helper()[FIELDS['Balance']])
    if withdraw_amount > balance:
        pretty_print_statement("Amount greater than balance!", Fore.RED)
        return False
    elif withdraw_amount < 1:
        pretty_print_statement("Amount Must be min 1!", Fore.RED)
        return False
    new_balance = balance-withdraw_amount
    update_query = {"$set": {FIELDS["Balance"]: new_balance}}
    db_operation(
        DB_COLLECTION, operation='u', condition={FIELDS['Account_number']: ACCOUNT_NUMBER}, data=update_query)
    pretty_print_statement("Withdraw success!", color=Fore.GREEN)
    statement()
    return True


def quit():
    pretty_print_statement("Quitting!", '*', 8, color=Fore.YELLOW)
    return True


states = {  # Emulate frontend using cli
    1: {
        'query':
        lambda: input(
            "create_account/login? (c/l),(q/cls): ")
            .strip().lower(),
        'functions': {
            'c': {'f': create, 's': 1},
            'l': {'f': login, 's': 2},
            'cls': {'f': clear_terminal, 's': 1},
            'q': {'f': quit, 's': 0},
        }
    },
    2: {
        'query':
        lambda: input(
            "deposit/withdraw/statement/logout? (d/w/s/l),(q/cls): ")
            .strip().lower(),
        'functions': {
            'd': {'f': deposit, 's': 2},
            'w': {'f': withdraw, 's': 2},
            's': {'f': statement, 's': 2},
            'l': {'f': logout, 's': 1},
            'cls': {'f': clear_terminal, 's': 2},
            'q': {'f': quit, 's': 0},
        }
    },
}


def state_manager(state):
    state_obj = states[state]
    response = state_obj['query']()
    if response in state_obj['functions']:
        success = False
        success = state_obj['functions'][response]['f']()
        if success:
            state = state_obj['functions'][response]['s']
    return state


def main():
    # innit db
    global DB_COLLECTION
    DB_COLLECTION = db_init()
    pretty_print_statement(
        "Banking App (use cls to clear and q to quit)", '*', 10, Fore.GREEN)
    state = 1
    while state:
        state = state_manager(state)


main()  # Execution starts here
