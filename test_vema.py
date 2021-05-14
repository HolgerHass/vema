import pytest
import vema
from colorama import Fore


@pytest.fixture
def inventory():
    database = [
        {"id": 1, "name": "Pinot Noir", "price": 4.50, "stock": 1},
        {"id": 2, "name": "Red Bull + Vodka", "price": 3.50, "stock": 2},
        {"id": 3, "name": "Soy Milk", "price": 1.00, "stock": 0},
    ]
    inv = vema.Inventory(product_list=database)
    return inv


def decolor(s):
    return (
        s.replace(Fore.YELLOW, "")
        .replace(Fore.RED, "")
        .replace(Fore.GREEN, "")
        .replace(Fore.RESET, "")
    )


def test_inv_list_products(inventory):
    result = inventory.list_products()
    result = decolor(result)
    expected = """  id  name                price    stock
----  ----------------  -------  -------
   1  Pinot Noir            4.5        1
   2  Red Bull + Vodka      3.5        2
   3  Soy Milk              1          0"""

    assert result == expected


def test_inv_retrieve_product(inventory):
    print(inventory.list_products())
    func = inventory.retrieve_product
    # amount in cent!
    assert func(1, 400)[0] == None  # too expensive
    amnt, msg = func(1, -200)
    assert amnt == None
    assert decolor(msg) == "Insufficient funds."
    amnt, msg = func(4, 400)
    assert amnt == None  # id unknown
    assert decolor(msg) == "No product with id 4."
    amnt, msg = func(3, 400)
    assert amnt == None  # sold out
    assert decolor(msg) == "Product 3 (Soy Milk) is sold out."
    amnt, msg = func(1, 500)
    assert amnt == 450  # works
    assert msg == "You retrieved 1 Pinot Noir for the price of €4.50."
    assert func(1, 500)[0] == None  # now sold out
    assert func(2, 500)[0] == 350  # well, then sth else


def test_amount_to_coins():
    coins = {5, 10, 20, 50, 100}
    func = vema.VendingMachineModel.amount_to_coins
    assert func(5, coins, prettify=False) == [5]
    assert func(15, coins, prettify=False) == [10, 5]
    assert func(20, coins, prettify=False) == [20]
    assert func(35, coins, prettify=False) == [20, 10, 5]
    assert func(45, coins, prettify=False) == [20, 20, 5]
    assert func(45, coins, prettify=True) == ["20ct", "20ct", "5ct"]
    assert func(85, coins, prettify=False) == [50, 20, 10, 5]
    assert func(90, coins, prettify=False) == [50, 20, 20]
    assert func(100, coins, prettify=False) == [100]
    assert func(140, coins, prettify=False) == [100, 20, 20]
    assert func(0, coins, prettify=False) == []
    assert func(2, coins, prettify=False) == None


def test_vmm_insert_money(inventory):
    vm = vema.VendingMachineModel(inventory=inventory)
    assert vm.balance == 0
    assert vm.insert_money(4.75) == 4.75  # returns the new balance
    assert vm.balance_eur == 4.75
    assert vm.insert_money(2) == 6.75
    assert vm.balance_eur == 6.75
    vm.insert_money(0)
    assert vm.balance_eur == 6.75
    vm.insert_money(-2)  # ignore neg
    assert vm.balance_eur == 6.75
    vm.insert_money(0.2498)  # cut cent fractions => 24ct
    assert vm.balance_eur == 6.99


def test_vmm_return_coins(inventory):
    vm = vema.VendingMachineModel(inventory=inventory)
    vm.insert_money(4.75)
    assert vm.balance_eur == 4.75
    assert vm.return_coins(prettify=False) == [100, 100, 100, 100, 50, 20, 5]
    assert vm.balance_eur == 0


def test_vmm_buy_product(inventory):
    vm = vema.VendingMachineModel(inventory=inventory)
    amnt, msg = vm.buy_product(1)
    assert amnt == None
    vm.insert_money(4.75)
    amnt, msg = vm.buy_product(1)
    assert amnt == 450
    assert vm.return_coins() == ["20ct", "5ct"]
    vm.insert_money(3.50)
    amnt, msg = vm.buy_product(2)
    assert amnt == 350
