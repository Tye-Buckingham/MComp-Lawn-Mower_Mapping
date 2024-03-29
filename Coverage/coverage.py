"""

This module is used to generate a complete
coverage path for an autonomous lawn-mower.

The module will be run on the server,
with the ordered GPS points being
sent to the robot for traversal/surveying

"""

import math
import random
from enum import Enum
from random import randrange

import geopandas
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pyclipper
import utm
from shapely.geometry import LineString, Point, Polygon
from surveytoolbox.bdc import bearing_distance_from_coordinates
from surveytoolbox.cbd import coordinates_from_bearing_distance
from surveytoolbox.config import BEARING, EASTING, ELEVATION, NORTHING
from surveytoolbox.fmt_dms import format_as_dms


def midpoint(p1, p2):
    return np.array([[(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]])


def gradient(p1, p2):
    return ((p2[1] - p1[1]) / (p2[0] - p1[0]))


def utm_bearing(p1, p2):
    dist = bearing_distance_from_coordinates(
        {
            EASTING: p1[0],
            NORTHING: p1[1],
            ELEVATION: 0
        }, {
            EASTING: p2[0],
            NORTHING: p2[1],
            ELEVATION: 0
        })
    return dist['bg']


def utm_dist(p1, p2):
    dist = bearing_distance_from_coordinates(
        {
            EASTING: p1[0],
            NORTHING: p1[1],
            ELEVATION: 0
        }, {
            EASTING: p2[0],
            NORTHING: p2[1],
            ELEVATION: 0
        })
    return dist['dist_2d']


def remove_intermediate_points(points, length):
    """Remove points that lie between two points that are a given
    distance away.

    This functions removes points which are close together and on the
    same line. This is to reduce the memory requirements of the route.
    Less points may result in worse accuracy so testing to find an
    optimal median is encouraged.

    Args:
        points: The [x, y] points of the traversal route.
    """
    j = 1
    i = 0
    new = np.empty((0, 2))
    while j < len(points) - 1 and i < len(points) - 1:
        new = np.vstack([new, points[i, :]])
        new = np.vstack([new, points[j, :]])
        while (points[i, 0] == points[j, 0] or points[i, 1]
               == points[j, 1]) and j < len(points) - 1 and math.dist(
                   points[i], points[j]) < length:
            if utm_dist(points[i], new[-1]) > utm_dist(points[i], points[j]):
                break
            new[-1] = points[j]
            j += 1

        i = j
        j = j + 1

    return new


def contained_y(bounds, y):
    """Checks if a point is contained within a bounding box's y axis

    Args:
        bounds: The bounding box
        y: The point to check

    Returns:
        True if the point is within and False if not
    """
    return bounds[1] < y < bounds[3]


def contained_x(bounds, x):
    """Checks if a point is contained within the bounding box's x axis

    Args:
        bounds: The bounding box
        x: The point to check

    Returns:
        True if the point is within and False if not
    """
    return bounds[2] > x > bounds[0]


def graph(points, height, width, overlap, up_down, left_right):
    """Generates the graph required for TSP from the generated from
    Quantise

    Args:
        points: The points from Quantise, will be used as nodes in the
            graph
        height: The height of the robot
        width: The width of the robot
        overlap: Overlap of the given route
        up_down: The factor to favour up-down over left-right movement to generate
              overlapping routes.
        left_right: The factor to favour left-right over up-down movement to generate
              overlapping routes.

    Returns:
        An undirected weighted graph to be used in TSP
    """

    g = nx.Graph()
    edges = list(tuple())
    # Way too close, make the list some form of hash map
    print("Processing " + str(len(points)) + " points into graph")
    p = 0
    for i in points:

        left = ((i[0] - (width * overlap), i[1]))
        if left in points:
            edges.append(
                tuple((i, left, math.dist([i[0], i[1]], [left[0], left[1]]) *
                       left_right)))

        right = ((i[0] + (width * overlap), i[1]))
        if left in points:
            edges.append(
                tuple(
                    (i, right, math.dist([i[0], i[1]], [right[0], right[1]]) *
                     left_right)))

        up = (([i[0], i[1] + height]))
        if left in points:
            edges.append(
                tuple((i, up,
                       math.dist([i[0], i[1]], [up[0], up[1]]) * up_down)))

        down = (([i[0], i[1] - height]))
        if left in points:
            edges.append(
                tuple((i, down,
                       math.dist([i[0], i[1]], [down[0], down[1]]) * up_down)))

    print("Adding " + str(len(edges)) + " edges to graph")
    for edge in edges:
        g.add_edge(tuple(edge[0]), tuple(edge[1]), weight=edge[2])

    return g


def bounding_box(shape):
    """Creates a rectangular box which wholey contains the given shape

    Args:
        shape: The shape to produce a bounding box for
    """
    min_x = shape[:, 0].min()
    max_x = shape[:, 0].max()
    min_y = shape[:, 1].min()
    max_y = shape[:, 1].max()

    # bounds_shape = np.array([[min_x, min_y], [min_x, max_y], [max_x, min_y],
    #                          [max_x, max_y]])
    return np.array([min_x, min_y, max_x, max_y])


def quantise(shape, height, width, overlap, nogos):
    """Quantises a shape within a bounding box

    Each point will be the centroid of a box the size of the robot.

    Args:
        shape: The perimeter of the shape to quantise
        height: The height of the robot
        width: The width of the robot
        overlap: The desired overlap of the route

    Returns:
        A list of centroids contained within the given shape
    """

    x_buff = width / 2
    y_buff = height / 2
    bounds = bounding_box(shape)
    min_x = shape[:, 0].min()
    min_y = shape[:, 1].min()
    x = min_x + x_buff
    y = min_y + y_buff
    points = set()
    poly = Polygon(shape)
    nogo_polys = list(map(Polygon, nogos))
    while contained_y(bounds, y):
        while contained_x(bounds, x):
            p = Point(x, y)
            in_nogo = False
            for i in range(len(nogo_polys)):
                if nogo_polys[i].contains(p):
                    in_nogo = True
                    break
            if poly.contains(p) and in_nogo == False:
                points.add((x, y))
            x += width * overlap
        y += height
        x = min_x + x_buff

    return points


def to_xy(perimeter, nogos):
    """Converts the perimeters and nogo zones from GPS to UTM

    UTM is used as the presumed area the mower will work on will
    result in the Earth's curvature being negligible. UTM allows for
    quicker calculates of distance and line equations, whilst
    providing movement in metres and bearing - generally more useful
    for navigating the mower than GPS.

    Args:
        perimeter:
        nogos:

    Returns:
        Returns the converted shapes along with the UTM zones. Zones
        should be the same to reduce error, though it is very unlikely
        any traversal will cross these boundary lines.
    """
    xy_shape = perimeter
    xy_nogos = nogos
    zone_nums = []
    zone_lets = []
    for i in range(len(perimeter)):
        u = np.array(utm.from_latlon(perimeter[i, 0], perimeter[i, 1]))
        zone_nums.append(int(u[2]))
        zone_lets.append(u[3])
        xy_shape[i, 0] = u[0]
        xy_shape[i, 1] = u[1]

    for i in range(len(nogos)):
        for j in range(len(nogos[i])):
            u = np.array(utm.from_latlon(nogos[i][j, 0], nogos[i][j, 1]))
            zone_nums.append(int(u[2]))
            zone_lets.append(u[3])
            xy_nogos[i][j, 0] = u[0]
            xy_nogos[i][j, 1] = u[1]

    uniq_zone_lets = len(set(zone_lets))
    uniq_zone_nums = len(set(zone_nums))
    if uniq_zone_lets > 1 or uniq_zone_nums > 1:
        print(
            "More than one zone found, conversion calculations may not be accurate!"
        )
        print(zone_nums)
        print(zone_lets)

    return [xy_shape, xy_nogos, zone_nums, zone_lets]


def inner_outer(xy_per, xy_nogos, width):
    """Generate inner bounday for perimeter and outer boundary(s) for
    nogo zone(s)

    The perimeter uses an inner offset to prevent going beyond the
    given bounds. The nogo zones uses an outer offset to prevent the
    mower going out forbidden areas.

    Args:
        xy_per: The perimeter in UTM
        xy_nogos: A list of nogo zones in UTM
        width: The width of the robot

    Returns:
        Returns the new perimeters to be used in TSP
    """
    shape = np.append(xy_per, [xy_per[0, :]],
                      axis=0)  # Append last to first to close off shape

    clipper_offset = pyclipper.PyclipperOffset()
    coordinates_scaled = pyclipper.scale_to_clipper(shape)

    clipper_offset.AddPath(coordinates_scaled, pyclipper.JT_ROUND,
                           pyclipper.ET_CLOSEDPOLYGON)

    new_coordinates = clipper_offset.Execute(
        pyclipper.scale_to_clipper(-(width)))
    inner = np.array(pyclipper.scale_from_clipper(new_coordinates)
                     [0])  # New inner perimeter to avoid clipping outside
    simple_per = geopandas.GeoSeries([
        LineString(geopandas.points_from_xy(x=inner[:, 0], y=inner[:, 1])),
    ])

    simple_per = simple_per.simplify(0.1)

    # Do the same for each nogo-shape, but with a positive offset
    # rather too far away than too close
    outer_nogos = list(list(list()))
    for i in range(len(xy_nogos)):
        temp = np.append(xy_nogos[i], [xy_nogos[i][0, :]], axis=0)

        clipper_offset = pyclipper.PyclipperOffset()
        coordinates_scaled = pyclipper.scale_to_clipper(temp)

        clipper_offset.AddPath(coordinates_scaled, pyclipper.JT_ROUND,
                               pyclipper.ET_CLOSEDPOLYGON)

        new_coordinates = clipper_offset.Execute(
            pyclipper.scale_to_clipper((width / 2)))
        clipped = np.array(pyclipper.scale_from_clipper(new_coordinates)[0])
        simple_nogo = geopandas.GeoSeries([
            LineString(
                geopandas.points_from_xy(x=clipped[:, 0], y=clipped[:, 1])),
        ])
        simple_nogo = simple_nogo.simplify(0.1)
        outer_nogos.append(np.array(simple_nogo.geometry.iloc[0].coords))

    return [np.array(simple_per.geometry.iloc[0].coords), outer_nogos]


def close_shape(shape):
    shape = np.append(shape, [shape[0]], axis=0)
    return shape


def main():
    height = 0.3
    width = 0.3
    overlap = 0.75
    test_shape = np.array([])

    nogos = list(np.array([[]]))

    #######################################
    ####        Formatting Data        ####
    #######################################
    print("Formatting Data")
    test_shape = close_shape(test_shape)
    for i in range(len(nogos)):
        nogos[i] = close_shape(nogos[i])

    print("Converting to UTM")
    # To UTM
    try:
        [xy_per, xy_nogos, zone_nums, zone_lets] = to_xy(test_shape, nogos)
    except utm.error.OutOfRangeError:
        print("Point's arent UTM - assuming already in GPS")
        xy_per = test_shape
        xy_nogos = nogos

    print("Creating Inner and Outer Perimeters")
    # Create inner perimeter and outter nogo boundaries
    [inner, outer_nogos] = inner_outer(xy_per, xy_nogos, width)

    print("Quantising")
    # Quantise the in perimeter, checking for outer nogo-zones
    test_points = quantise(inner, height, width, overlap, outer_nogos)

    # Convert back to GPS - if needed
    # gps_points = xy_per
    # for i in range(len(xy_per)):
    #     gps = np.array(
    #         utm.to_latlon(xy_per[i, 0], xy_per[i, 1], zone_nums[0],
    #                       zone_lets[0]))
    #     gps_points[i, 0] = gps[0]
    #     gps_points[i, 1] = gps[1]

    print("Appending Points")
    # Append one point from inner perimeter and one from each nogo-zone
    # allowing TSP to link them together

    inner = np.append(inner, [inner[0, :]], axis=0)
    for i in inner:
        test_points.add((i[0], i[1]))
    for nogo in outer_nogos:
        for point in nogo:
            test_points.add((point[0], point[1]))

    # Need to refactor for the change to sets
    # inner = np.append(inner, [inner[0, :]], axis=0)
    # for i in range(len(outer_nogos)):
    #     test_points = np.concatenate((test_points, outer_nogos[i]))

    # test_points = np.append([inner[0, :]], test_points, axis=0)

    #######################################
    ####         Processing Data       ####
    #######################################
    print("Processing Data")
    # Graph the points
    test_graph = graph(test_points, height, width, overlap, 1.0, 1.5)
    print(test_graph)

    # Complete the TSP algorithm
    tsp = nx.approximation.traveling_salesman_problem(test_graph, cycle=True)
    tsp = np.array(tsp)
    print("First TSP Complete")

    # Adding some noise to a seperate set for testing of the traversal algorithm
    final_noise = tsp  # keep original for testing
    tsp = remove_intermediate_points(tsp, 10)  # reduced points
    final_route = np.concatenate((inner, tsp))

    # Graph the points
    test_graph = graph(test_points, height, width, overlap, 1.5, 1.0)
    print(test_graph)

    # Complete the TSP algorithm
    tsp = nx.approximation.traveling_salesman_problem(test_graph, cycle=True)
    tsp = np.array(tsp)
    print("Second TSP Complete")

    # Adding some noise to a seperate set for testing of the traversal algorithm
    final_noise = tsp  # keep original for testing
    tsp = remove_intermediate_points(tsp, 10)  # reduced points
    final_route = np.concatenate((final_route, tsp))

    # Need to define a home point, add to list, and ensure is same as start #
    # print(final_route[-1])
    # print(final_route[0])
    # assert ((final_route[-1] == final_route[0]).all())
    final_route = np.append(final_route, [final_route[0]], axis=0)

    #######################################
    ####  Plotting bounds and points   ####
    #######################################
    print("Plotting")
    # Display
    s = geopandas.GeoSeries([
        LineString(geopandas.points_from_xy(x=tsp[:, 0], y=tsp[:, 1])),
        LineString(geopandas.points_from_xy(x=inner[:, 0], y=inner[:, 1])),
    ])

    f, ax = plt.subplots()
    plt.axis('off')
    s.buffer(width / 2).plot(alpha=0.5, ax=ax)
    plt.plot(inner[:, 0], inner[:, 1])
    plt.plot(xy_per[:, 0], xy_per[:, 1])
    plt.plot(final_route[:, 0], final_route[:, 1], linewidth=0.1, color='red')

    plt.scatter(final_route[:, 0],
                final_route[:, 1],
                linewidth=0.1,
                color='green')
    plt.scatter(final_route[0, 0], final_route[0, 1], color='blue')
    for i in range(len(outer_nogos)):
        # plt.plot(outer_nogos[i][:, 0],
        #          outer_nogos[i][:, 1],
        #          linewidth=0.5,
        #          color='yellow')

        geopandas.GeoSeries([
            LineString(
                geopandas.points_from_xy(x=outer_nogos[i][:, 0],
                                         y=outer_nogos[i][:, 1])),
        ]).buffer(width / 2).plot(alpha=0.5, ax=ax)
        plt.plot(nogos[i][:, 0], nogos[i][:, 1], linewidth=1, color='red')

    try:
        plt.show()
    except:
        plt.savefig("./test.png")
    #######################################
    #### Saving the points for testing ####
    #######################################
    print("Saving")
    # final_route = np.append(inner, tsp, axis=0)
    # print(tsp)
    # final_noise = np.append(inner, to_noise, axis=0)
    # for nogo in outer_nogos:
    #     index = np.where(final_noise == nogo[0])
    #     final_noise = np.insert(final_noise, index, outer_nogos[i])
    #     index = np.argwhere(final_route == outer_nogos[i][0])
    #     final_route = np.insert(final_route, index, outer_nogos[i])

    # Saving route
    np.savetxt("../Map_Matching_Uniform/Noise_Tests/route.out",
               final_route,
               delimiter=',')
    np.savetxt("./out_route.out", final_route, delimiter=',')
    # Adding noise to simulate inaccuracy and errors
    for i in range(0, 100):
        fname = "../Map_Matching_Uniform/Noise_Tests/" + str(i) + "_route.out"
        # noise = np.random.normal(0, 0.15, final_route.shape)
        noise_route = np.empty(final_noise.shape, dtype=float)
        for j in range(len(final_noise)):
            if not any((final_route[:] == final_noise[j, :]).all(1)):
                noise_route[j, 0] = final_noise[j, 0] + random.uniform(
                    -0.50, 0.50)
                noise_route[j, 1] = final_noise[j, 1] + random.uniform(
                    -0.50, 0.50)
            else:
                noise_route[j, :] = final_noise[j, :]
        np.savetxt(fname, noise_route, delimiter=',')

    print(len(final_route))

    # Converting back to GPS (long, lat)
    # for i in range(len(final_route)):
    #     gps = np.array(
    #         utm.to_latlon(final_route[i, 0], final_route[i, 1], zone_nums[0],
    #                       zone_lets[0]))
    #     final_route[i, 0] = gps[0]
    #     final_route[i, 1] = gps[1]


if __name__ == "__main__":
    main()
