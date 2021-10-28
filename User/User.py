import json


class User:
    """docstring"""

    def __init__(self, id):
        f = open("users_data/" + id + ".json", 'r')
        self.user = json.load(f)
        f.close()

    def save(self):
        f = open("users_data/" + str(self.user['id']) + ".json", "w")
        json.dump(self.user, f)
        f.close()

    def get_favorite_stock(self, stock_name):
        favorite = list(
            filter(lambda favorite: favorite["name"].lower() == stock_name.lower(), self.user['favorites']))
        favorite = favorite[0] if len(favorite) > 0 else False
        return favorite

    def get_favorites(self):
        return self.user['favorites']

    def del_favorite_stock(self, stcok_name):
        favorite = self.get_favorite_stock(stcok_name)
        if favorite:
            if self.user['favorites'].count(favorite):
                self.user['favorites'].remove(favorite)
                return True
            else:
                return False
        else:
            return False

    def add_favorite(self, stock):
        # favorite = self.user['favorites']
        # if favorite['name'] or favorite['price'] or favorite['best_price']:
        #     self.user['favorites'].append({})
        # self.user['favorites'][-1]['name'] = stock.get('name')
        # self.user['favorites'][-1]['price'] = stock.get('price')
        # self.user['favorites'][-1]['best_price'] = stock.get('best_price')
        self.user['favorites'].append(
            {'name': stock.get('name'), 'price': stock.get('price'), 'best_price': stock.get('best_price')})

    def empty_favorites(self):
        return len(self.user['favorites']) == 0

    def clear_favorites(self):
        self.user['favorites'] = []
        return True
