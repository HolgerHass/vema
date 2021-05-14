from colorama import Fore
from tabulate import tabulate


DATABASE = [
    {"id": 1, "name": "Water", "price": 0.50, "stock": 10},
    {"id": 2, "name": "Coke", "price": 1.00, "stock": 10},
    {"id": 3, "name": "Diet Coke", "price": 1.20, "stock": 10},
    {"id": 4, "name": "Iced Tea", "price": 1.00, "stock": 10},
    {"id": 5, "name": "Chocolate", "price": 1.50, "stock": 10},
    {"id": 6, "name": "Candy", "price": 0.95, "stock": 10},
    {"id": 7, "name": "Chips", "price": 2.50, "stock": 10},
    {"id": 8, "name": "Espresso", "price": 1.20, "stock": 10},
    {"id": 9, "name": "Coffee", "price": 1.50, "stock": 10},
]

# 1 EUR, 0.5 EUR, 0.20 EUR, 0.10 EUR and 0.05 EUR
DEFAULT_COINS = {5, 10, 20, 50, 100}  # in ct


def msg_error(s):
    return Fore.RED + s + Fore.RESET


def msg_attn(s):
    return Fore.YELLOW + s + Fore.RESET


def msg_confirm(s):
    return Fore.GREEN + s + Fore.RESET


class Inventory:
    """Class responsible for managing a product inventory"""

    def __init__(self, product_list=None):
        """Inventory constructor

        Parameters
        ----------
        product_list : list(dict), optional
            Initial product list to use instead of the default one, by default None
        """
        pl = product_list if product_list is not None else DATABASE
        self._products = {p["id"]: p for p in pl}  # for faster lookup

    def list_products(self):
        """List products in the inventory

        Returns
        -------
        string
            formatted table with product list
        """
        col_names = list(self._products.values())[0].keys()
        rows = [x.values() for x in self._products.values()]
        return msg_attn(tabulate(rows, col_names))

    def retrieve_product(self, id, amount_ct):
        """Retrieve a product from the inventory

        Parameters
        ----------
        id : int
            product id
        amount_ct : int
            amount available in cent

        Returns
        -------
        tuple(int | None, str)
            amount spent in cent or `None` in case of failure; message containing information about success or source of failure
        """
        msg = None
        prod = self._products.get(id, None)
        if prod is None:
            msg = msg_error(f"No product with id {id}.")
            return None, msg
        if prod["stock"] == 0:
            msg = msg_error(f"Product {id} ({prod['name']}) is sold out.")
            return None, msg
        price_ct = int(prod["price"] * 100)
        if price_ct > amount_ct:
            msg = msg_error("Insufficient funds.")
            return None, msg

        prod["stock"] += -1  # prod mutable => inventory automatically updated
        msg = f"You retrieved 1 {prod['name']} for the price of €{prod['price']:.2f}."
        return price_ct, msg


class VendingMachineModel:
    """Model for a vending machine"""

    def __init__(self, initial_balance=0, inventory=None):
        self._inventory = inventory if inventory is not None else Inventory()
        self._balance = initial_balance
        self._coins = sorted(DEFAULT_COINS, reverse=True)

    @property
    def balance(self):
        return self._balance

    @property
    def balance_eur(self):
        return self._balance / 100

    @staticmethod
    def amount_to_coins(amount_ct, coin_set, prettify=True):
        """converts an amount into a list of coins

        Parameters
        ----------
        amount_ct : int
            amount to be split into coins
        coin_set : iterable(int)
            coin denominations available to calculate change
        prettify : bool, optional
            coin representation as formatted strings if `True`, by default True

        Returns
        -------
        list(int) | list(str) | None
            List of coins as int (e.g. 1€ = 100) or string. Returns `None` if correct change cannot be given with available coins.
        """
        coins = sorted(coin_set, reverse=True)
        result = list()
        rest = amount_ct
        for c in coins:
            result += [c] * (rest // c)
            rest = rest % c
        if rest != 0:
            return None
        if prettify:
            result = [f"{int(c/100)}€" if c >= 100 else f"{c}ct" for c in result]
        return result

    def _amount_to_coins(self, amount_ct, prettify=True):
        return self.amount_to_coins(amount_ct, self._coins, prettify)

    def insert_money(self, amount_eur):
        """Increases current balance by a certain amount in EUR

        Parameters
        ----------
        amount_eur : float
            Amount to add in EUR

        Returns
        -------
        float
            New balance in EUR after transaction
        """
        self._balance += int(max(0, (amount_eur * 100)))
        return self.balance / 100

    def return_coins(self, prettify=True):
        """Return remaining balance as coins, setting balance to 0.

        Parameters
        ----------
        prettify : bool, optional
            coin representation as formatted strings if `True`, by default True

        Returns
        -------
        list(int) | list(str) | None
            List of coins as int (e.g. 1€ = 100) or string. Returns `None` if correct change cannot be given with available coins.
        """
        result = self._amount_to_coins(self.balance, prettify=prettify)
        self._balance = 0
        return result

    def buy_product(self, id):
        """Buy one item of a product

        Parameters
        ----------
        id : int
            product id

        Returns
        -------
        tuple(int | None, str)
            amount spent in cent or `None` in case of failure; message containing information about success or source of failure
        """
        amount_paid_ct, msg = self._inventory.retrieve_product(id, self.balance)
        if amount_paid_ct is not None:
            self._balance -= amount_paid_ct
        return amount_paid_ct, msg

    def list_products(self):
        """List products in the vending machine

        Returns
        -------
        string
            formatted table with product list
        """
        return self._inventory.list_products()


def insert_money(vmm: VendingMachineModel):
    try:
        amount = float(input(msg_attn("Amount in €: ")))
        vmm.insert_money(amount)
    except ValueError:
        print(msg_error("Please type in a number."))
        return


def return_money(vmm: VendingMachineModel):
    coin_list = vmm.return_coins()
    print(msg_attn("Don't forget to take your change!\n" + str(coin_list)))


def list_products(vmm):
    print(vmm.list_products())


def buy_product(vmm: VendingMachineModel):
    try:
        id = int(input(msg_attn("Product ID: ")))
    except ValueError:
        print(msg_error("Please input a number."))
        return

    _, msg = vmm.buy_product(id)
    print(msg)


def get_user_action():
    choices = {
        "i": insert_money,
        "r": return_money,
        "l": list_products,
        "b": buy_product,
    }
    print("--------------------")
    print("[i] Insert money")
    print("[r] Return money")
    print("[l] List products")
    print("[b] Buy product")
    print("--------------------")
    print()
    choice = input("[i], [r], [l] or [b]?\n").lower()
    return choices.get(choice, None)


def main():
    print("=== Vending Machine ===")
    vmm = VendingMachineModel()

    try:
        while True:
            print()
            print(f"Current balance: €{vmm.balance_eur:.2f}")
            act = get_user_action()
            if act is not None:
                act(vmm)
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
