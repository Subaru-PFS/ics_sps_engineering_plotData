from math import floor, ceil, log10
import numpy as np

def transformCoord2Log(display_coord, ax, ax2, inv=False):
    xmin, xmax = ax2.get_xlim()
    ymin, ymax = ax2.get_ylim()
    pix_ymin = int(ceil(ax2.transData.transform((xmin, ymin))[1]))
    pix_ymax = int(floor(ax2.transData.transform((xmax, ymax))[1]))
    pix_xmin = int(ceil(ax2.transData.transform((xmin, ymin))[0]))
    pix_xmax = int(floor(ax2.transData.transform((xmax, ymax))[0]))

    ax_xmin, ax_xmax = ax.get_ylim()
    ax_xmin = log10(ax_xmin)
    ax_xmax = log10(ax_xmax)
    slope = (ax_xmax - ax_xmin) / (pix_ymax - pix_ymin)
    offset = (ax_xmin + ax_xmax - slope * (pix_ymax + pix_ymin)) / 2

    ax_ymin, ax_ymax = ax.get_xlim()
    slope2 = (ax_ymax - ax_ymin) / (pix_xmax - pix_xmin)
    offset2 = (ax_ymin + ax_ymax - slope2 * (pix_xmax + pix_xmin)) / 2
    if not inv:
        time = display_coord[0] * slope2 + offset2
        res = 10 ** (display_coord[1] * slope + offset)
        return [time, res]
    else:
        if display_coord[1] > 0:
            pix_x = (display_coord[0] - offset2) / slope2
            pix_y = (log10(display_coord[1]) - offset) / slope
            return [pix_x, pix_y]
        return None


def indFinder(array, t0):
    res = np.searchsorted(array, t0) if t0 < array[-1] else len(array) - 1
    return res


def computeScale(t, (xdata, ydata)):
    table_x = np.nan * np.ones(3 * t.shape[0])
    table_y = np.nan * np.ones(3 * t.shape[0])
    for i in range(t.shape[0] - 1):
        m, n = np.searchsorted(xdata, t[i]), np.searchsorted(xdata, t[i + 1])
        if (n - m) > 0:
            inter = ydata[m:n]
            mean = np.mean(inter)
            res = np.sort(m + np.array([np.argmin(np.abs(inter - mean)), np.argmax(inter - mean), np.argmax(mean - inter)]))
            table_x[3 * i: 3 * i + 3] = xdata[res]
            table_y[3 * i: 3 * i + 3] = ydata[res]

    return table_x[~np.isnan(table_x)], table_y[~np.isnan(table_y)]

