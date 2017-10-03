import numpy as np

from curve import Curve


class Derivate(Curve):
    enum = {0: 60, 1: 3600}

    def __init__(self, parent, graph, label, type, ylabel, unit, tableName, keyword, combo, ranges, spinbox, cmb_unit):
        self.spinbox = spinbox
        self.integ_time = self.spinbox.value()
        self.coeff = Derivate.enum[cmb_unit.currentIndex()]
        super(Derivate, self).__init__(parent, graph, label, type, ylabel, unit, tableName, keyword, combo, ranges)
        self.yscale = "linear"

    def getData(self, getStarted=False, dtime=3300):

        if getStarted:
            return_values = self.parent.parent.db.getData(self.tableName, self.keyword, self.last_id, self.end_id,
                                                          False)
            if type(return_values) is int:
                self.parent.parent.showError(return_values)
            else:
                slope = self.computeSlope(*return_values)
                if slope is not None:
                    new_id, dates, values = slope
                    self.set_data(np.append(self.get_xdata(), dates), np.append(self.get_ydata(), values))
                    self.getExtremum(values, firstTime=True)
                    self.last_id = new_id
                    if self.dataset == "real_time":
                        self.watcher.start()

        else:
            return_values = self.parent.parent.db.getData(self.tableName, self.keyword, self.last_id, self.end_id,
                                                          False)
            if return_values in [-5, -4]:
                pass
            elif type(return_values) is int:
                self.watcher.stop()
                self.parent.parent.showError(return_values)
            else:
                slope = self.computeSlope(*return_values)
                if slope is not None:
                    new_id, dates, values = slope
                    self.set_data(np.append(self.get_xdata(), dates), np.append(self.get_ydata(), values))
                    self.getExtremum(values)
                    self.graph.updateLine(self.currLine, dates, values, dtime)
                    self.last_id = new_id

    def computeSlope(self, all_id, dates, values):
        i = 0
        a = 0
        result = []
        end = False
        while i < len(dates):
            while self.integ_time - (dates[i] - dates[a]) > 2:
                i += 1
                if i == len(dates):
                    end = True
                    break
            if end:
                last_id = all_id[a - 1]
                break
            else:
                result.append([a, i])
                a += 1
        if result:
            result_date = np.array([(dates[res[0]] + dates[res[1]]) / 2 for res in result])
            result_value = np.array(
                [self.coeff * (values[res[1]] - values[res[0]]) / (dates[res[1]] - dates[res[0]]) for res in result])

            return last_id, self.parent.parent.db.convertArraytoAstro(result_date), result_value
