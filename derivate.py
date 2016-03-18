import numpy as np

from curve import Curve


class Derivate(Curve):
    def __init__(self, parent, graph, label, type, ylabel, unit, tableName, keyword, combo, spinbox):
        self.spinbox = spinbox
        super(Derivate, self).__init__(parent, graph, label, type, ylabel, unit, tableName, keyword, combo)

    def getData(self):
        integ_time = self.spinbox.value()
        i = 0
        a = 0
        result = []
        end = False
        end_id = "Now" if self.dataset == "real_time" else self.parent.parent.db.getrowrelative2Date(self.tableName,
                                                                                                     'id',
                                                                                                     self.graph.numDate + self.parent.parent.calendar.spinboxDays.value() * 86400,
                                                                                                     True)

        all_id, dates, values = self.parent.parent.db.getData(self.tableName, self.keyword, self.last_id, end_id, False)

        if type(dates) == np.ndarray:
            if dates.any() and integ_time > 15:
                while i < len(dates):
                    while integ_time - (dates[i] - dates[a]) > 2:
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
                    result_date, result_value = np.zeros(len(result)), np.zeros(len(result))
                    for i in range(len(result)):
                        result_date[i] = self.parent.parent.db.convertfromAstro(
                            (dates[result[i][0]] + dates[result[i][1]]) / 2)
                        result_value[i] = 60 * (values[result[i][1]] - values[result[i][0]]) / (
                            dates[result[i][1]] - dates[result[i][0]])

                    self.set_data(np.append(self.get_xdata(), result_date), np.append(self.get_ydata(), result_value))
                    self.last_id = last_id
                    if not self.firstCall:
                        self.graph.updateLine(self.getLine(), self)
                    elif self.dataset == "real_time":
                        self.watcher.start()
            else:
                self.parent.parent.showError(-4)
                self.last_id = 0
        else:
            if self.firstCall:
                self.parent.parent.showError(dates)
                self.last_id = 0

        self.firstCall = False
