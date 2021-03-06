from abc import ABCMeta, abstractmethod
import Monstr.Core.DB as DB
import Monstr.Core.Utils as Utils



# ,----------------------.
# |BaseNodule            |
# |----------------------|
# |+string name          |
# |+obj table_schemas    |
# |----------------------|
# |+void Initialize()    |
# |+obj PrepareRetrieve()|
# |+obj Retrieve()       |
# |+obj InsertToDB()     |
# |+obj Analyze()        |
# |+obj React()          |
# |+obj Run()            |
# `----------------------'


class BaseModule():
    __metaclass__ = ABCMeta
    
    name = None
    table_schemas = None
    tables = None
    db_handler = None

    journal_schema = (DB.Column('id', DB.Integer, primary_key=True),
                      DB.Column('module', DB.String(64)),
                      DB.Column('time', DB.DateTime(True)),
                      DB.Column('result', DB.String(32)),
                      DB.Column('step', DB.String(32)),
                      DB.Column('description', DB.Text),)

    def _create_journal_row(self, result, step=None, error=None):
        row = {'module': self.name,
               'time': Utils.get_UTC_now(),
               'result': result,
               'step': step,
               'description': (type(error).__name__ + ': ' + error.message) if error is not None else None
        }
        return row

    def _create_params(self, default_params, params):
        result = {}
        for key in default_params:
            if key not in params:
                result[key] = default_params[key]
            else:
                result[key] = type(default_params[key])(params[key])
        return result


    rest_links = {}

    def __init__(self):
        self.db_handler = DB.DBHandler()

    def Initialize(self):
        if self.name is None:
            raise "Module require name"
        if self.table_schemas is None:
            raise "Module require schemas list"
        self.tables = self.db_handler.initialize(self.table_schemas, self.name)


    def PrepareRetrieve(self):
        return {}

    @abstractmethod
    def Retrieve(self, params):
        pass

    def InsertToDB(self, data):
        for schema in data:
            table = self.tables[schema]
            self.db_handler.bulk_insert(table, data[schema])        

    def ExecuteCheck(self):
        journal = self.db_handler.getOrCreateTable('monstr_Journal', self.journal_schema)
        try:
            self.Initialize()
        except Exception as e:
            row = self._create_journal_row('Fail', 'Initialize', e)
            self.db_handler.insert(journal, row)
            return

        try:
            params = self.PrepareRetrieve()
        except Exception as e:
            row = self._create_journal_row('Fail', 'PrepareRetrieve', e)
            self.db_handler.insert(journal, row)
            return

        try:
            data = self.Retrieve(params)
        except Exception as e:
            row = self._create_journal_row('Fail', 'Retrieve', e)
            self.db_handler.insert(journal, row)
            return

        try:
            self.InsertToDB(data)
        except Exception as e:
            row = self._create_journal_row('Fail', 'InsertToDB', e)
            self.db_handler.insert(journal, row)
            return

        row = self._create_journal_row('Success')
        self.db_handler.insert(journal, row)
        
