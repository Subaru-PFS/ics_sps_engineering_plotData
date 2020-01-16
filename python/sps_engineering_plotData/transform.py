import numpy as np
from matplotlib.dates import num2date


def indFinder(array, elem):
    ind = np.searchsorted(array, elem) if elem < array[-1] else len(array) - 1
    return ind


def computeScale(t, data):
    xdata, ydata = data
    table_x = np.nan * np.ones(3 * t.shape[0])
    table_y = np.nan * np.ones(3 * t.shape[0])
    for i in range(t.shape[0] - 1):
        m, n = np.searchsorted(xdata, t[i]), np.searchsorted(xdata, t[i + 1])
        if (n - m) > 0:
            inter = np.argsort(ydata[m:n])
            res = np.sort(m + np.array([inter[0], inter[len(inter) // 2], inter[-1]]))

            table_x[3 * i: 3 * i + 3] = xdata[res]
            table_y[3 * i: 3 * i + 3] = ydata[res]

    min, max = np.searchsorted(xdata, t[0]) - 1, np.searchsorted(xdata, t[-1]) + 1

    if min > 0:
        table_x = np.insert(table_x, 0, xdata[min])
        table_y = np.insert(table_y, 0, ydata[min])
    if max < len(xdata):
        table_x = np.append(table_x, xdata[max])
        table_y = np.append(table_y, ydata[max])

    return table_x[~np.isnan(table_x)], table_y[~np.isnan(table_y)]


def make_format(ax2, ax1):
    # current and other are axes
    def format_coord(x, y):
        display_coord = ax2.transData.transform((x, y))
        inv = ax1.transData.inverted()

        ax_coord = inv.transform(display_coord)

        # unit1 = ax1.get_ylabel().split(' ')[1] if ax1.get_lines() else ''
        # unit2 = ax2.get_ylabel().split(' ')[1] if ax2.get_lines() else ''
        #
        # date = num2date(x).isoformat()[:19]
        # val1 = 'y1%s = %g' % (unit1, ax_coord[1]) if unit1 else ''
        # val2 = 'y2%s = %g' % (unit2, y) if unit2 else ''

        date = num2date(x).isoformat()[:19]
        val1 = 'y1 = %g' % ax_coord[1] if ax1.get_lines() else ''
        val2 = 'y2 = %g' % y if ax2.get_lines() else ''

        return '   '.join([date, val1, val2])

    return format_coord
