/**
 * @file   queue.h
 * @author T. Buckingham
 * @date   Thu Feb 16 10:50:59 2023
 * 
 * @brief  Queue system used to track the number of out-of-bonds occurences.
 *
 * When a defined percentage of points are outside
 * the area of inaccuracy the system will decide it is off course.
 * A small number of points may be an error and so multiple are
 * used to confirm whether the robot is off course or not.
 * 
 */

#ifndef QUEUE_H
#define QUEUE_H

#include <inttypes.h>
#include <stdint.h>
#include <math.h>
#include <stdio.h>

#define QUEUE_LEN 10
#define ON_COURSE  0
#define OFF_COURSE 1

struct queue {
	int8_t inside[QUEUE_LEN];
	int8_t length;
};

/** 
 * @brief Simple helper function to print the contents of the queue.
 * 
 * @param q The queue to iterate over.
 */
void print_q(struct queue* q);

/** 
 * @brief Shift all values in the queue to the left and add the new value onto the start.
 *
 *
 * @param q The queue to process
 * @param inside A 1 or 0, depending if the robot was outside of the boundary.
 */
void enqueue(struct queue* q, int8_t inside);

/** 
 * @brief Based on the percentage of out-of-bounds points determine if the robot is off course.
 *
 *
 * @param q The queue holding the stored out-of-bounds values.
 * 
 * @return Whether the robot is OFF_COURSE or ON_COURSE
 */
int8_t is_off_course(struct queue* q);

/** 
 * @brief A simple helper function to set all values of the queue to 0
 * 
 * @param q The queue to reset.
 */
void flush(struct queue* q);

#endif
