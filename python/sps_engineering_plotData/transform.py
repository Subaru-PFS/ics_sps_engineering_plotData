import numpy as np
from matplotlib.dates import num2date

N_POINTS = 2000


def indFinder(array, elem):
    ind = np.searchsorted(array, elem) if elem < array[-1] else len(array) - 1
    return ind


def lttb(xdata, ydata, tmin, tmax, n_out=N_POINTS):
    """Largest Triangle Three Buckets downsampling.

    Clips to the visible range [tmin, tmax] first (so zooming reveals more
    detail from the raw data), then downsamples to n_out points. One point
    of margin is kept on each side for clean line rendering at the edges.
    """
    # clip to visible range with one point of margin on each side
    i0 = max(np.searchsorted(xdata, tmin) - 1, 0)
    i1 = min(np.searchsorted(xdata, tmax) + 1, len(xdata))
    xdata, ydata = xdata[i0:i1], ydata[i0:i1]

    n_in = len(xdata)
    if n_in <= n_out:
        return xdata, ydata

    # always keep first and last
    selected = np.empty(n_out, dtype=np.intp)
    selected[0] = 0
    selected[-1] = n_in - 1

    bucket_size = (n_in - 2) / (n_out - 2)
    a = 0

    for i in range(n_out - 2):
        b_start = int((i + 1) * bucket_size) + 1
        b_end = min(int((i + 2) * bucket_size) + 1, n_in - 1)

        # centroid of the next bucket — used as the fixed far point
        c_start = b_end
        c_end = min(int((i + 3) * bucket_size) + 1, n_in - 1)
        avg_x = xdata[c_start:c_end].mean() if c_start < c_end else xdata[-1]
        avg_y = ydata[c_start:c_end].mean() if c_start < c_end else ydata[-1]

        ax, ay = xdata[a], ydata[a]
        bx = xdata[b_start:b_end]
        by = ydata[b_start:b_end]

        if len(bx) == 0:
            selected[i + 1] = a
            continue

        # pick the point that forms the largest triangle (skip the /2, irrelevant for argmax)
        areas = np.abs((ax - avg_x) * (by - ay) - (bx - ax) * (avg_y - ay))
        selected[i + 1] = b_start + np.argmax(areas)
        a = selected[i + 1]

    return xdata[selected], ydata[selected]


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
