#include <stdbool.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static void	on_alarm(int sig)
{
	(void)sig;
}

int	sandbox(void (*f)(void), unsigned int timeout, bool verbose)
{
	struct sigaction	sa;
	struct sigaction	old;
	pid_t				pid;
	int					status;

	pid = fork();
	if (pid == -1)
		return (-1);
	if (pid == 0)
	{
		f();
		exit(0);
	}
	// no SA_RESTART: the alarm makes waitpid() fail with EINTR
	sa.sa_handler = on_alarm;
	sa.sa_flags = 0;
	sigemptyset(&sa.sa_mask);
	sigaction(SIGALRM, &sa, &old);
	alarm(timeout);
	if (waitpid(pid, &status, 0) == -1)
	{
		if (errno != EINTR)
			return (sigaction(SIGALRM, &old, NULL), -1);
		kill(pid, SIGKILL);
		waitpid(pid, NULL, 0);
		sigaction(SIGALRM, &old, NULL);
		if (verbose)
			printf("Bad function: timed out after %u seconds\n", timeout);
		return (0);
	}
	alarm(0);
	sigaction(SIGALRM, &old, NULL);
	if (WIFEXITED(status) && WEXITSTATUS(status) == 0)
	{
		if (verbose)
			printf("Nice function!\n");
		return (1);
	}
	if (WIFEXITED(status))
	{
		if (verbose)
			printf("Bad function: exited with code %d\n", WEXITSTATUS(status));
		return (0);
	}
	if (WIFSIGNALED(status))
	{
		if (verbose)
			printf("Bad function: %s\n", strsignal(WTERMSIG(status)));
		return (0);
	}
	return (-1);
}
