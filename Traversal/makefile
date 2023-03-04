TARGET 	= map
LIBS	=
CC	= gcc
CFLAGS  = -g -Wall -Wpedantic -Werror -Wconversion -Wextra -std=c11 -O3
TFLAGS  = -g  
RM      = rm -f

default: all

test: test.c map.c map.h queue.c queue.h test_data.h ./munit/munit.c ./munit/munit.h
	$(CC) $(TFLAGS) -o map test.c map.c queue.c ./munit/munit.c -lm

all: map

map: map.c map.h main.c queue.c queue.h test_data.h
	$(CC) $(CFLAGS) -o map main.c map.c queue.c -lm

