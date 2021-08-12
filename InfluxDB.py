""""""
from influxdb import InfluxDBClient
from secrets import InfluxDB as IDBSecrets

TEMP_DATABASE = 'exampleDB'

# TODO: Fix this class

class IDBController:
    """ Enter Comment """

    def __init__(self):
        """ Enter Comment """
        self.client = InfluxDBClient()

    def create_db(self):
        """ If no database to connect to, we can create a new one before we initialise"""
        # return InfluxDBClient.create_database()
        self.client.create_database(TEMP_DATABASE)
        pass

    def connect_db(self):
        self.client = InfluxDBClient(host='localhost',
                                     port=8086,
                                     username=IDBSecrets.USERNAME,
                                     password=IDBSecrets.PASSWORD)

    def view_db(self):
        print("Database Store:")
        print(self.client.get_list_database())


def main():
    print("Hello")
    database = IDBController()
    database.connect_db()
    database.view_db()
    InfluxDBClient.


if __name__ == '__main__':
    main()
