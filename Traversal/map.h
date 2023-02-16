/**
 * @file   map.h
 * @author T. Buckingham
 * @date   Thu Feb 16 11:00:05 2023
 * 
 * @brief  The main functions for mapping the robot to the given route.
 * 
 * The functions used to determine the line between two points,
 * the robot's distance from the given line, and other error checking
 * functions such as impossible movement.
 *
 *
 */

#ifndef MAP_H
#define MAP_H

#include <math.h>
#include <stdint.h>
#include <inttypes.h>
#include "queue.h"


#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifndef FLT_EPSILON
#define FLT_EPSILON 1.19209290E-07F
#endif

struct line_equation {
	long double m;
	long double c;
};

struct point {
	long double x;
	long double y;
	// double;
};

/** 
 * @brief A helper function to return the line equation between two points.
 * 
 * @param line The line struct to hold the values.
 * @param a Point a on a plane
 * @param b Pount b on a plane
 * 
 * @return Error checking value.
 */
uint8_t get_line(struct line_equation* line, struct point* a, struct point* b);

/** 
 * @brief A helper function to determine a points distance from a given line.
 * 
 * @param line The line the robot is currently traversing.
 * @param a The robot's current position.
 * 
 * @return The distance a is from line
 */
long double distance_from_line(struct line_equation* line, struct point* a);

/** 
 * @brief Determines the robot has reached the next checkpoint in route.
 * 
 * @param a The robot's current position.
 * @param next The next point the robot is currently heading towards.
 * 
 * @return Wether the next point has been reached or not.
 */
int8_t is_next_point(struct point* a, struct point* next);

/** 
 * @brief A helper function to determine if the robot is outside the inaccuracy boundary.
 * 
 * @param line The line the robot is currently traversing.
 * @param a The robot's current position.
 * 
 * @return Whether the robot is outside the given buffer or not.
 */
int8_t is_outside_buffer(struct line_equation* line, struct point* a);

/** 
 * @brief Determines if the movement between points is physically possible.
 *
 * Given the speed, time and distance; is it possible for the robot to move in such a way.
 *
 * @param a The robot's previous location.
 * @param b The robot's current position.
 * @param time The time between point a and b.
 * 
 * @return Whether the movement was possible or not. 
 */
int8_t is_possible(struct point* a, struct point* b, float time);

#endif
