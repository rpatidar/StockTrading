"""
TODO: This is partial class,
"""


class MoneyManager(object):
    def __abs__(self, starting_amount):
        self.portfolio = {}

    pass

    def get_balance(self):

        pass

    def can_take_risk(self, amount):

        pass

    def get_allowed_risk(self):

        pass

    def update_profit_loss(self, stock, amount):

        pass

    def update_portfolio(self, date, stock, quantity, price, type):
        stock_positions = self.portfolio.get(stock)
        if stock_positions == None:
            self.portfolio[stock] = [
                {"quantity": quantity, "type": type, "date": date, "price": price}
            ]
        else:
            if type == "buy":
                for position in stock_positions:
                    if position["type"] == "sell":
                        self.exit_existing_position(position, quantity, price)
            elif type == "sell":
                for position in stock_positions:
                    if position["type"] == "buy":
                        self.exit_existing_position(position, quantity)

    def exit_existing_position(self, position, quantity, price, type):
        quantity_changed = 0
        if quantity <= position["quantity"]:
            position["quantity"] = quantity_changed = position["quantity"] - quantity
            position["quantity"] = quantity_changed
            pl = (
                position["price"] - price
                if type == "buy"
                else price - position["price"]
            )
            self.update_profit_loss(pl)
        else:
            quantity = quantity - position["quantity"]
            position["quantity"] = 0

    pass

    def release_quantity(self, date, stock, amount, quantity):

        pass


pass
