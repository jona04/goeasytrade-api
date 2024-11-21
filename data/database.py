from pymongo import MongoClient, errors
from constants.defs import MONGO_CONN
from collections import defaultdict


class DataDB:
    def __init__(self):
        self.client = MongoClient(MONGO_CONN)
        self.db = self.client.forex_learning

    def test_connection(self):
        print(self.db.list_collection_names())

    def add_one(self, collection, ob):
        try:
            _ = self.db[collection].insert_one(ob)
        except errors.InvalidOperation as error:
            print("add one error", error)

    def add_many(self, collection, list_ob):
        try:
            _ = self.db[collection].insert_many(list_ob)
        except errors.InvalidOperation as error:
            print("add many error", error)

    def query_all_list(self, collection, limit=100, **kargs):
        try:
            cursor = self.db[collection].find(kargs, {"_id": 0}).limit(limit)

            result = defaultdict(list)
            for item in cursor:
                for key, value in item.items():
                    result[key].append(value)

            return result
        except errors.InvalidOperation as error:
            print("query_all error", error)

    def query_all(self, collection, limit=100, **kargs):
        try:
            data = []
            r = self.db[collection].find(kargs, {"_id": 0}).limit(limit)
            for item in r:
                data.append(item)
            return data
        except errors.InvalidOperation as error:
            print("query_all error", error)

    def query_single(self, collection, **kargs):
        try:
            return self.db[collection].find_one(kargs, {"_id": 0})
        except errors.InvalidOperation as error:
            print("query_single error", error)

    def query_distinct(self, collection, key):
        try:
            return self.db[collection].distinct(key)
        except errors.InvalidOperation as error:
            print("query_single error", error)

    def delete_single(self, collection, **kargs):
        try:
            _ = self.db[collection].delete_one(kargs)
        except errors.InvalidOperation as error:
            print("delete_many error", error)

    def delete_many(self, collection, **kargs):
        try:
            _ = self.db[collection].delete_many(kargs)
        except errors.InvalidOperation as error:
            print("delete_many error", error)

    def update_one(self, collection, filter_criteria, update_values, upsert=False):
        """
        Atualiza um documento na coleção especificada.
        :param collection: Nome da coleção.
        :param filter_criteria: Critérios de filtro para encontrar o documento.
        :param update_values: Valores para atualizar.
        :param upsert: Se True, cria o documento caso ele não exista.
        """
        try:
            result = self.db[collection].update_one(filter_criteria, {"$set": update_values}, upsert=upsert)
            return result
        except Exception as error:
            print("Erro no update_one:", error)
            return None

    def update_many(self, collection, filter_criteria, update_values):
        try:
            _ = self.db[collection].update_many(
                filter_criteria, {"$set": update_values}
            )
        except errors.InvalidOperation as error:
            print("update_many error:", error)


    def update_partial_close(self, open_order_id, closed_percentage, remaining_quantity, break_even_price):
        """
        Atualiza os detalhes de um trade após o fechamento parcial.
        :param open_order_id: ID único do trade ativo.
        :param closed_percentage: Percentual da posição já encerrada.
        :param remaining_quantity: Quantidade restante após a parcial.
        :param break_even_price: Novo preço ajustado para Break Even.
        """
        try:
            self.update_one(
                "trades",
                {"_id": open_order_id},
                {
                    "closed_percentage": closed_percentage,
                    "remaining_quantity": remaining_quantity,
                    "break_even_price": break_even_price,
                    "partial_close_triggered": True
                }
            )
            print(f"Trade {open_order_id} atualizado após parcial.")
        except Exception as e:
            print(f"Erro ao atualizar trade {open_order_id} após parcial: {e}")

    def query_partial_trades(self):
        """
        Retorna os trades ativos que ainda não tiveram fechamento parcial.
        """
        try:
            return self.query_all("trades", activate=True, partial_close_triggered=False)
        except Exception as e:
            print(f"Erro ao consultar trades para fechamento parcial: {e}")
            return []

    def update_trade_status(self, open_order_id=None, **kwargs):
        """
        Atualiza ou cria o status de um trade na coleção central `trades`.
        :param open_order_id: ID da ordem de abertura (usado como chave principal).
        :param kwargs: Outros campos a atualizar (take_profit, stop_loss, etc.).
        """
        try:
            filter_criteria = {"_id": open_order_id}
            update_data = {"$set": kwargs}
            self.update_one("trades", filter_criteria, update_data, upsert=True)
            print(f"Trade {open_order_id} atualizado com sucesso.")
        except Exception as e:
            print(f"Erro ao atualizar trade {open_order_id}: {e}")
