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
            cursor = self.db[collection].find(kargs).limit(limit)

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
            r = self.db[collection].find(kargs).limit(limit)
            for item in r:
                # Converte ObjectId para string
                if "_id" in item:
                    item["_id"] = str(item["_id"])
                data.append(item)
            return data
        except errors.InvalidOperation as error:
            print("query_all error", error)

    def query_single(self, collection, **kargs):
        try:
            result = self.db[collection].find_one(kargs)
            if result and "_id" in result:
                # Converte o ObjectId para string
                result["_id"] = str(result["_id"])
            return result
        except errors.InvalidOperation as error:
            print("query_single error", error)
            return None
        
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
            # Verifica se $set já está no update_values e ajusta se necessário
            if "$set" in update_values:
                update_values = update_values["$set"]
            
            result = self.db[collection].update_one(
                filter_criteria,
                {"$set": update_values},  # Encapsula corretamente
                upsert=upsert
            )
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
