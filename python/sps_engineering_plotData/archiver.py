from functools import partial

from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager


class ArchiverHandler(DatabaseManager):
    def __init__(self, *args, **kwargs):
        DatabaseManager.__init__(self, *args, **kwargs, doConnect=False)
        self.connectionBroke = False

    def fetchone(self, *args, **kwargs):
        func = partial(DatabaseManager.fetchone, self, *args, **kwargs)
        return self.fixConnAndGo(func)

    def fetchall(self, *args, **kwargs):
        func = partial(DatabaseManager.fetchall, self, *args, **kwargs)
        return self.fixConnAndGo(func)

    def fixConnAndGo(self, func, doRetry=True):
        doRetry = not self.connectionBroke and doRetry

        try:
            df = func()
            self.connectionBroke = False
            return df
        except ValueError:
            raise
        except Exception as e:
            if doRetry:
                self.close()
                return self.fixConnAndGo(func, doRetry=False)
            else:
                if not self.connectionBroke:
                    self.connectionBroke = True
                    raise UserWarning(str(e))
                else:
                    raise ValueError(e)
