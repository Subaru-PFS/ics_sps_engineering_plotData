import six
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT

import figureoptions
from qt_compat import QtWidgets


class myNavigationToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, parent):
        NavigationToolbar2QT.__init__(self, canvas, parent)

    def isZoomed(self):
        if self._active == "ZOOM":
            return 1
        else:
            return 0

    def isPanned(self):
        if self._active == "PAN":
            return 1
        else:
            return 0

    def getViewEmpty(self):
        return self._views.empty()

    def edit_parameters(self):
        allaxes = self.canvas.figure.get_axes()
        if len(allaxes) == 1:
            axes = allaxes[0]
        else:
            titles = []
            for axes in allaxes:
                title = axes.get_title()
                ylabel = axes.get_ylabel()
                label = axes.get_label()
                if title:
                    fmt = "%(title)s"
                    if ylabel:
                        fmt += ": %(ylabel)s"
                    fmt += " (%(axes_repr)s)"
                elif ylabel:
                    fmt = "%(axes_repr)s (%(ylabel)s)"
                elif label:
                    fmt = "%(axes_repr)s (%(label)s)"
                else:
                    fmt = "%(axes_repr)s"
                titles.append(fmt % dict(title=title,
                                         ylabel=ylabel, label=label,
                                         axes_repr=repr(axes)))
            item, ok = QtWidgets.QInputDialog.getItem(
                self.parent, 'Customize', 'Select axes:', titles, 0, False)
            if ok:
                axes = allaxes[titles.index(six.text_type(item))]
            else:
                return

        figureoptions.figure_edit(axes, self)
