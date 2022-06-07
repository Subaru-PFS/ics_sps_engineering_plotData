from matplotlib import cbook
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT

try:
    from matplotlib.backend_bases import _Mode

    oldVersion = False
except ImportError:
    oldVersion = True


class NStack(cbook.Stack):
    def __init__(self):
        cbook.Stack.__init__(self)

    def updateHome(self, limits):
        if not len(self._elements):
            return

        home = self._elements[0]
        for axes, newView in limits.items():
            view, (pos_orig, pos_active) = home[axes]
            home[axes] = newView, (pos_orig, pos_active)

        self._elements[0] = home


class NavigationToolbar(NavigationToolbar2QT):
    def __init__(self, graph, plotWindow):
        NavigationToolbar2QT.__init__(self, graph, plotWindow)
        self._nav_stack = NStack()

    def isZoomed(self):
        ret = self.isZoomed1() if oldVersion else self.isZoomed2()
        return ret

    def isPanned(self):
        ret = self.isPanned1() if oldVersion else self.isPanned2()
        return ret

    def isZoomed1(self):
        return self._active == 'ZOOM'

    def isPanned1(self):
        return self._active == 'PAN'

    def isZoomed2(self):
        return self.mode == _Mode.ZOOM

    def isPanned2(self):
        return self.mode == _Mode.PAN

    def setNewHome(self, limits):
        self._nav_stack.updateHome(limits)
