import six
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT

import figureoptions
from matplotlib.backends.qt_compat import QtWidgets


class NavigationToolbar(NavigationToolbar2QT):
    def __init__(self, graph, plotWindow):
        NavigationToolbar2QT.__init__(self, graph, plotWindow)

    def isZoomed(self):
        if self._active == 'ZOOM':
            return 1
        else:
            return 0

    def isPanned(self):
        if self._active == 'PAN':
            return 1
        else:
            return 0

    def setNewHome(self, limits):

        saved = [view for view in self._views]
        self._views.clear()

        self._views.push(limits)
        for i in range(1, len(saved)):
            self._views.push(saved[i])

    def getViewEmpty(self):
        return self._views.empty()

    def edit_parameters(self):
        allaxes = self.canvas.figure.get_axes()
        if not allaxes:
            QtWidgets.QMessageBox.warning(
                self.parent, "Error", "There are no axes to edit.")
            return
        if len(allaxes) == 1:
            axes = allaxes[0]
        else:
            titles = []
            for axes in allaxes:
                name = (axes.get_title() or
                        " - ".join(filter(None, [axes.get_xlabel(),
                                                 axes.get_ylabel()])) or
                        "<anonymous {} (id: {:#x})>".format(
                            type(axes).__name__, id(axes)))
                titles.append(name)
            item, ok = QtWidgets.QInputDialog.getItem(
                self.parent, 'Customize', 'Select axes:', titles, 0, False)
            if ok:
                axes = allaxes[titles.index(six.text_type(item))]
            else:
                return

        figureoptions.figure_edit(axes, self)
