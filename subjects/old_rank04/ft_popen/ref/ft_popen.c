#include <unistd.h>
#include <stdlib.h>

int	ft_popen(const char *file, char *const argv[], char type)
{
	int		fds[2];
	pid_t	pid;

	if (!file || !argv || (type != 'r' && type != 'w'))
		return (-1);
	if (pipe(fds) == -1)
		return (-1);
	pid = fork();
	if (pid == -1)
	{
		close(fds[0]);
		close(fds[1]);
		return (-1);
	}
	if (pid == 0)
	{
		// 'r': the command writes into the pipe; 'w': it reads from it
		if (dup2(type == 'r' ? fds[1] : fds[0], type == 'r' ? 1 : 0) == -1)
			exit(1);
		close(fds[0]);
		close(fds[1]);
		execvp(file, argv);
		exit(1);
	}
	close(type == 'r' ? fds[1] : fds[0]);
	return (type == 'r' ? fds[0] : fds[1]);
}
