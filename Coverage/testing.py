"""

This module is used to generate a complete
coverage path for an autonomous lawn-mower.

The module will be run on the server,
with the ordered GPS points being
sent to the robot for traversal/surveying

"""

import geopandas
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from shapely.geometry import LineString, Point, Polygon

for select in range(99, 100):
    try:
        perfect_route = np.loadtxt(
            "../Map_Matching_Uniform/Noise_Tests/route.out",
            dtype=float,
            delimiter=",")

        noise_route = np.loadtxt("../Map_Matching_Uniform/Noise_Tests/" +
                                 str(select) + "_route.out",
                                 dtype=float,
                                 delimiter=",")
        test_route = np.loadtxt("./Results/" + str(select) + "_route.out",
                                dtype=float,
                                delimiter=",")

        s = geopandas.GeoSeries([
            LineString(
                geopandas.points_from_xy(x=perfect_route[:, 0],
                                         y=perfect_route[:, 1]))
        ])

        # plt.scatter(test_route[:, 0], test_route[:, 1], color='red', ax=ax)
        # plt.plot(noise_route[:, 0],
        #          noise_route[:, 1],
        #          '--o',
        #          color='green',
        #          alpha=0.4)
        # plt.plot(perfect_route[:, 0],
        #          perfect_route[:, 1],
        #          '-o',
        #          color='black',
        #          alpha=0.8)

        x = noise_route[:, 0]
        y = noise_route[:, 1]
        red = np.empty((0, 2))

        fig = plt.figure()
        ax = fig.add_subplot(111)
        s.buffer(0.15).plot(alpha=0.2, ax=ax)
        line = ax.plot([], [], '-o')[0]
        scat = ax.scatter([], [], s=60)

        ax.set_xlim(np.min(x), np.max(x))
        ax.set_ylim(np.min(y), np.max(y))

        def animate(i, factor):
            global red
            line.set_xdata(x[:i])
            line.set_ydata(y[:i])
            if any((noise_route[i] == x).all() for x in test_route):
                red = np.concatenate((red, [[x[i], y[i]]]))
                scat.set_offsets(red)
                scat.set_color('red')
            else:
                line.set_color('blue')

            return line, scat,

        K = 0.75
        ani = animation.FuncAnimation(fig,
                                      animate,
                                      frames=len(x),
                                      fargs=(K, ),
                                      interval=1000,
                                      blit=True)

        ani.save("Demo_slow.gif", dpi=300, writer=PillowWriter(fps=10))
        plt.show()

    except IndexError:  # If the file is empty
        continue
