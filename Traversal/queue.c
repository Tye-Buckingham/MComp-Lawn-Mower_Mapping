#include "queue.h"

void enqueue(struct queue* q, int8_t inside)
{

	for(int i = 0; i < (q->length - 1); i++) {
		q->inside[i + 1] = q->inside[i + 1] ^ q->inside[i];
		q->inside[i] = q->inside[i + 1] ^ q->inside[i];
		q->inside[i + 1] = q->inside[i + 1] ^ q->inside[i];
	}
	q->inside[q->length - 1] = inside;
	
	return;
}

void print_q(struct queue* q)
{
	for(int i = 0; i < q->length; i++) {
		int ret = printf("%d,%c", q->inside[i], (i == (q->length - 1)) ? '\n' : ' ');
		if(ret < 0) {
			perror("Error printing queue member\n");
		}
	}
	
	return;
}

void flush(struct queue* q)
{
	for(int i = 0; i < q->length; i++) {
		q->inside[i] = 0;
	}
	return;
}

float per_on_course(struct queue* q)
{
	float res = q->length;
	for(int i = 0; i < q->length; i++) {
		res -= q->inside[i];
	}
	res /= q->length;
	return res;

}

int8_t is_off_course(struct queue* q)
{
	int8_t res = ON_COURSE;
	if(per_on_course(q) < 0.6) {
		res = OFF_COURSE;
	}
	
	return res;
}
