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


def dichot(x, array, ind_inf=0, ind_sup=None):
    if ind_sup is None:
        ind_sup = len(array) - 1
    if (ind_sup - ind_inf) == 1:
        if abs(array[ind_sup] - x) > abs(array[ind_inf] - x):
            return ind_inf
        else:
            return ind_sup
    else:
        if x < array[ind_inf + (ind_sup - ind_inf) / 2]:
            return dichot(x, array, ind_inf, (ind_inf + (ind_sup - ind_inf) / 2))
        else:
            return dichot(x, array, (ind_inf + (ind_sup - ind_inf) / 2), ind_sup)


def indFinder(t0, array):
    if t0 < array[0]:
        ind = 0
    elif t0 > array[-1]:
        ind = len(array) - 1
    else:
        ind = dichot(t0, array)
    return ind


def computeScale(t, (xdata, ydata)):
    table_x = np.nan * np.ones(3 * len(t))
    table_y = np.nan * np.ones(3 * len(t))
    for i in range(len(t) - 1):
        m, n = indFinder(t[i], xdata), indFinder(t[i + 1], xdata)
        inter = ydata[m:n]
        if len(inter) > 0:
            mean = np.mean(inter)
            ind_mean = m + np.argmin(np.abs(inter - mean))
            ind_min = m + np.argmax(inter - mean)
            ind_max = m + np.argmax(mean - inter)
            res = sorted(
                [(xdata[ind], ydata[ind]) for ind in
                 [ind_mean, ind_min, ind_max]],
                key=lambda x: x[0])
            table_x[3 * i: 3 * i + 3] = [data[0] for data in res]
            table_y[3 * i: 3 * i + 3] = [data[1] for data in res]

    return table_x[~np.isnan(table_x)], table_y[~np.isnan(table_y)]
