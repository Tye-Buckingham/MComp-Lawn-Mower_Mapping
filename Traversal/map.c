#define _USE_MATH_DEFINES
#include "map.h"

#define MAX_SPEED 0.6f // 2 mph in m/s

uint8_t get_line(struct line_equation* line, struct point* a, struct point* b)
{
	if((b->x - a->x) == 0) {
		a->x += FLT_EPSILON;
	}
	line->m = (b->y - a->y) / (b->x - a->x);
	line->c = a->y - (line->m * a->x);
	return 0;
}

long double distance_from_line(struct line_equation* line, struct point* a)
{
	return (fabsl ( a->y - (line->m * a->x) - line->c)) /
		(sqrtl (1 + (line->m * line->m)));
}

int8_t is_outside_buffer(struct line_equation* line, struct point* a)
{
	int8_t ret = ON_COURSE;
	//printf("%F, ", distance_from_line(line, a));
	long double dist = distance_from_line(line, a);
	
	if(dist > 0.15F) { // 0.2 m -> 20 cm
		// printf("dist: %F\n", dist);
		ret = OFF_COURSE;
	}
	return ret;
}

int8_t is_next_point(struct point* a, struct point* next)
{
	int8_t res = -1;
	if( powl(a->x - next->x, 2) + powl(a->y - next->y, 2) < powl(0.2, 2)) {
		res = 0;
	}
	return res;	
}

int8_t is_possible(struct point* a, struct point* b, float time)
{
	int8_t res = 0;
	// Distance needs to account for the +- 20 cm inaccuracy
	long double distance = sqrtl((powl((b->x - a->x), 2) + powl((b->y - a->y), 2)));
	// If the needed speed needed to traverse the distance is more than the max speed
	//printf("%F\n", (distance / time));
	if((distance / time) > MAX_SPEED) {
		res = 1;
	}
	return res;
}

