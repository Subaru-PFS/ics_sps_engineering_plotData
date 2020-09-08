from matplotlib import cbook
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT


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
        if self._active == 'ZOOM':
            return 1
        else:
            return 0

    def isPanned(self):
        if self._active == 'PAN':
            return 1
        else:
            return 0

    def edit_parameters(self):
        self.canvas.fig.editAxes = True
        try:
            NavigationToolbar2QT.edit_parameters(self)
        except RuntimeError as e:
            print('INSTRM-1071 :', e)
        self.canvas.fig.editAxes = False

    def setNewHome(self, limits):
        self._nav_stack.updateHome(limits)
