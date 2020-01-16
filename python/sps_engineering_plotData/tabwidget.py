__author__ = 'alefur'
from PyQt5.QtWidgets import QTabWidget, QInputDialog, QMessageBox, QTabBar, QLineEdit

from sps_engineering_plotData.tab import Tab


class EditableTabTitle(QLineEdit):
    def __init__(self, tabBar, index):
        QLineEdit.__init__(self, tabBar.tabText(index))
        self.setParent(tabBar)

        rect = tabBar.tabRect(index)
        self.move(rect.x(), rect.y())

        self.tabBar = tabBar
        self.index = index

        self.editingFinished.connect(self.editTitle)

    def editTitle(self):
        self.tabBar.setTabText(self.index, self.text())
        self.setVisible(False)
        self.tabBar.tabTitleVisible = False


class PTabBar(QTabBar):
    def __init__(self, parent):
        QTabBar.__init__(self)
        self.setParent(parent)
        self.tabTitleVisible = False
        self.setTabsClosable(True)

    def mouseDoubleClickEvent(self, QMouseEvent):
        if not self.tabTitleVisible:
            tabTitle = EditableTabTitle(self, self.currentIndex())
            tabTitle.setVisible(True)
            self.tabTitleVisible = True


class PTabWidget(QTabWidget):
    def __init__(self, mainwindow):
        QTabWidget.__init__(self)
        self.mainwindow = mainwindow
        self.activeTab = False
        self.tabCloseRequested.connect(self.delTab)
        self.currentChanged.connect(self.changeTab)
        # self.setTabsClosable(True)

        self.createTabBar()

    def createTabBar(self):
        tabBar = PTabBar(self)
        self.setTabBar(tabBar)

    def dialogTab(self):

        text, ok = QInputDialog.getText(self, 'Name your tab', 'Name')
        if ok:
            text = 'untitled' if not text else text
            self.addNameTab(name=text)

    def addNameTab(self, name):
        widget = Tab(self)
        self.addTab(widget, name)
        self.setCurrentWidget(widget)

    def delTab(self, k):
        reply = QMessageBox.question(self, 'Message',
                                     'Are you sure to close this window?', QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.removeTab(k)

    def changeTab(self):
        currWidget = self.currentWidget()

        if self.activeTab:
            self.activeTab.stop()

        self.activeTab = currWidget

        if self.activeTab is not None:
            self.activeTab.restart()

    def tabText(self, index=None):
        index = self.currentIndex() if index is None else index
        return QTabWidget.tabText(self, index)
