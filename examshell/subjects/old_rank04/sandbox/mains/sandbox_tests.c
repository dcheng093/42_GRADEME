// sandbox tests: one kind of function per argv[1]
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

int	sandbox(void (*f)(void), unsigned int timeout, bool verbose);

static void	nice_fn(void) {}
static void	nice_prints(void) { printf("(the function prints this)\n"); }
static void	exits_1(void) { exit(1); }
static void	exits_42(void) { exit(42); }
static void	exits_0(void) { exit(0); }
static void	segfault(void) { volatile int *p = NULL; *p = 42; }
static void	aborts(void) { abort(); }
static void	fpe(void) { raise(SIGFPE); }
static void	killed(void) { kill(getpid(), SIGKILL); }
static void	loops(void) { while (1) ; }
static void	sleeps(void) { sleep(10); }
static void	quick(void) { usleep(200000); }
static void	ignores_alarm(void) { signal(SIGALRM, SIG_IGN); alarm(1); while (1) ; }
static void	forks_and_waits(void) { pid_t p = fork(); if (p == 0) exit(3); waitpid(p, NULL, 0); }

int	main(int argc, char **argv)
{
	struct { const char *name; void (*f)(void); unsigned int timeout; } tests[] = {
		{"a nice function", nice_fn, 2},
		{"a nice function that prints", nice_prints, 2},
		{"exit(1)", exits_1, 2},
		{"exit(42)", exits_42, 2},
		{"exit(0) is nice", exits_0, 2},
		{"a segfault", segfault, 2},
		{"abort()", aborts, 2},
		{"SIGFPE", fpe, 2},
		{"killed by SIGKILL", killed, 2},
		{"an infinite loop (timeout 1)", loops, 1},
		{"sleep(10) (timeout 1)", sleeps, 1},
		{"0.2s of work (timeout 2) is nice", quick, 2},
		{"ignores SIGALRM and loops (timeout 1)", ignores_alarm, 1},
		{"forks a child of its own", forks_and_waits, 2},
	};
	int	i;
	int	ret;
	int	zombies = 0;

	setvbuf(stdout, NULL, _IONBF, 0);
	if (argc != 3)
		return (1);
	i = atoi(argv[1]);
	if (i < 0 || i >= (int)(sizeof(tests) / sizeof(*tests)))
		return (1);
	printf("--- %s, verbose %s\n", tests[i].name, argv[2]);
	ret = sandbox(tests[i].f, tests[i].timeout, argv[2][0] == '1');
	printf("--- returned %d\n", ret);
	// any child still there, running or zombie, was not waited for
	for (pid_t r; (r = waitpid(-1, NULL, WNOHANG)) != -1; zombies++)
		if (r == 0)
		{
			usleep(100000);
			if (waitpid(-1, NULL, WNOHANG) == 0)
			{
				zombies++;
				break ;
			}
		}
	printf("--- processes left behind: %d\n", zombies);
	return (0);
}
