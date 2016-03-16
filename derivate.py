import numpy as np

from curve import Curve


class Derivate(Curve):
    def __init__(self, parent, graph, label, type, ylabel, unit, row, column, combo, spinbox):
        self.spinbox = spinbox
        super(Derivate, self).__init__(parent, graph, label, type, ylabel, unit, row, column, combo)

    def getData(self):
        integ_time = self.spinbox.value()
        i = 0
        a = 0
        result = []
        end = False
        if self.dataset == "real_time":
            [date, value], all_id = self.parent.parent.db.getData_Numpy(self.row, self.column, self.last_id, None,
                                                                        False)
        else:
            end_id = self.parent.parent.db.getrowrelative2Date(self.row, 'id',
                                                               self.graph.numDate + self.parent.parent.calendar.spinboxDays.value() * 86400)
            [date, value], all_id = self.parent.parent.db.getData_Numpy(self.row, self.column, self.last_id, end_id,
                                                                        False)
        if type(date) == np.ndarray:
            if date.any() and integ_time > 15:
                while i < len(date):
                    while integ_time - (date[i] - date[a]) > 2:
                        i += 1
                        if i == len(date):
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
                            (date[result[i][0]] + date[result[i][1]]) / 2)
                        result_value[i] = 60 * (value[result[i][1]] - value[result[i][0]]) / (
                            date[result[i][1]] - date[result[i][0]])

                    self.set_data(np.append(self.get_xdata(), result_date), np.append(self.get_ydata(), result_value))
                    self.last_id = last_id
                    if not self.firstCall:
                        self.graph.updateLine(self.getLine(), self)
                    elif self.dataset == "real_time":
                        self.watcher.start()
            else:
                self.parent.parent.showError(-4)
        else:
            if self.firstCall: self.parent.parent.showError(date)

        self.firstCall = False
