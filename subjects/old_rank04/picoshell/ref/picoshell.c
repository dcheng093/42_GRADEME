#include <unistd.h>
#include <stdlib.h>
#include <sys/wait.h>

int	picoshell(char **cmds[])
{
	int		prev_in;
	int		fds[2];
	int		status;
	int		ret;
	pid_t	pid;

	ret = 0;
	prev_in = -1;
	for (int i = 0; cmds[i]; i++)
	{
		fds[0] = -1;
		fds[1] = -1;
		if (cmds[i + 1] && pipe(fds) == -1)
		{
			ret = 1;
			break ;
		}
		pid = fork();
		if (pid == -1)
		{
			if (fds[0] != -1)
				(close(fds[0]), close(fds[1]));
			ret = 1;
			break ;
		}
		if (pid == 0)
		{
			if (prev_in != -1 && (dup2(prev_in, 0) == -1 || close(prev_in) == -1))
				exit(1);
			if (fds[1] != -1 && (dup2(fds[1], 1) == -1 || close(fds[1]) == -1 || close(fds[0]) == -1))
				exit(1);
			execvp(cmds[i][0], cmds[i]);
			exit(1);
		}
		// the parent keeps only the read end, for the next command
		if (prev_in != -1)
			close(prev_in);
		if (fds[1] != -1)
			close(fds[1]);
		prev_in = fds[0];
	}
	if (prev_in != -1)
		close(prev_in);
	while (wait(&status) > 0)
		if (WIFEXITED(status) && WEXITSTATUS(status) != 0)
			ret = 1;
	return (ret);
}
