#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fenv.h>

#include "queue.h"
#include "map.h"
#include "test_data.h"

int x = 0;
int y = 1;

void test_with_data(int i)
{
	
	int node = 0;
	int point = 0;
	FILE* fp;
	char filename[101];
	snprintf(filename, 100, "../Coverage/Results/%d_route.out", i);
	fp = fopen(filename, "w");
	struct queue q = { .inside = {0}, .length = QUEUE_LEN };
	struct line_equation line = { .m = 0, .c = 0 };
	struct point current_node = { .x = route[0][x], .y = route[0][y] };
	struct point next_node = { .x = route[1][x], .y = route[1][y] };
	
	if(get_line(&line, &current_node, &next_node) != 0) { // get line from start node to next
		perror("Error");
		fclose(fp);
		return;
	}
	while((node < route_len) && (point < positions_len)) { // while still has nodes - will only check for route in application
		struct point current_position = { .x = positions[point][x], .y = positions[point][y] };
		if(is_next_point(&current_position, &next_node) == 0) {
			//printf("[%F, %F],\n", current_position.x, current_position.y);
			node += 1;
			current_node.x = route[node][x]; current_node.y = route[node][y];
			next_node.x = route[node + 1][x]; next_node.y = route[node + 1][y];
			get_line(&line, &current_node, &next_node);
		}
		// if is_out_buffer then perform error checks
		int8_t outside = is_outside_buffer(&line, &current_position);
		/* if(outside == 1 || outside == 0) { */
		/* 	struct point previous_position = { .x = positions[point - 1][x], .y = positions[point - 1][y] }; */
		/* 	if(is_possible(&current_position, &previous_position, 0.75f) == 1) { */
		/* 		// printf("[%F, %F],\n", current_position.x, current_position.y); */
		/* 		fprintf(fp, "%F, %F\n", current_position.x, current_position.y); */
		/* 		outside = 0; */
		/* 	} */
		/* } */
		/* if(outside == 1) { */
		/* 	fprintf(fp, "%F, %F\n", current_position.x, current_position.y); */
		/* } */
		// if not noticeable error - then need to check trajectories - add flags as we need the next two values
		// if not error then add 1
		// print_q(&q);
		
		enqueue(&q, outside);
		if(is_off_course(&q) == OFF_COURSE) {
			fprintf(fp, "%LF, %LF\n", current_position.x, current_position.y);
			// flush(&q);
			// printf("[%F, %F],\n", current_position.x, current_position.y);
		}
		
		point++;
	}
	if(node < route_len) {
		printf("%d : %d\n", node, route_len);
	}
	fclose(fp);
	return;
}

void read_positions(int i)
{
	for(int j = 0; j < 50000; j++) {
		positions[j][0] = 0;
		positions[j][1] = 0;
	}
	positions_len = 0;
	FILE * fp;
	char * line = NULL;
	size_t len = 0;
	ssize_t read;
	char filename[101];
	snprintf(filename, 100, "./Noise_Tests/%d_route.out", i); 
	fp = fopen(filename, "r");
	if (fp == NULL)
		exit(EXIT_FAILURE);

	while ((read = getline(&line, &len, fp)) != -1) {
		char* token = strtok(line, ",");
		positions[positions_len][0] = strtold(token, NULL);
		token = strtok(NULL, ",");
		positions[positions_len][1] = strtold(token, NULL);
		positions_len++;
		
	}
	free(line);
	fclose(fp);
	
	return;
}

void read_route(void)
{
	FILE * fp;
	char * line = NULL;
	size_t len = 0;
	ssize_t read;
	char* token = NULL;

	fp = fopen("./Noise_Tests/route.out", "r");
	if (fp == NULL)
		exit(EXIT_FAILURE);

	while ((read = getline(&line, &len, fp)) != -1) {
		token = strtok(line, ",");
		route[route_len][0] = strtold(token, NULL);
		token = strtok(NULL, ",");
		route[route_len][1] = strtold(token, NULL);
		route_len++;
	}
	free(line);
	fclose(fp);

	return;
}

int main(void)
{
	
	feenableexcept(FE_ALL_EXCEPT & ~FE_INEXACT);
	//test_line_and_circle();
	//test_queue();
	read_route();
	for(int i = 0; i < 100; i++) {
		read_positions(i);
		test_with_data(i);
	}
	
	
	return 0;
}
