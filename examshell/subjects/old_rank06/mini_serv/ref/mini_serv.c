#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <stdio.h>

typedef struct s_client
{
	int		id;
	char	*buf;  // what arrived after the last '\n'
}	t_client;

static t_client	g_clients[FD_SETSIZE];
static int		g_used[FD_SETSIZE];
static fd_set	g_all;
static fd_set	g_rd;
static fd_set	g_wr;
static int		g_max;
static int		g_next_id;
static int		g_listen;

static void	fatal(void)
{
	write(2, "Fatal error\n", 12);
	exit(1);
}

static int	extract_message(char **buf, char **msg)
{
	char	*newbuf;
	int		i;

	*msg = 0;
	if (*buf == 0)
		return (0);
	i = 0;
	while ((*buf)[i])
	{
		if ((*buf)[i] == '\n')
		{
			newbuf = calloc(1, strlen(*buf + i + 1) + 1);
			if (newbuf == 0)
				return (-1);
			strcpy(newbuf, *buf + i + 1);
			*msg = *buf;
			(*msg)[i + 1] = 0;
			*buf = newbuf;
			return (1);
		}
		i++;
	}
	return (0);
}

static char	*str_join(char *buf, char *add)
{
	char	*newbuf;
	int		len;

	len = buf ? strlen(buf) : 0;
	newbuf = malloc(len + strlen(add) + 1);
	if (newbuf == 0)
		return (0);
	newbuf[0] = 0;
	if (buf != 0)
		strcat(newbuf, buf);
	free(buf);
	strcat(newbuf, add);
	return (newbuf);
}

// to every client but `except` that select() says can take it: a client
// that doesn't read is skipped, never waited for
static void	broadcast(int except, const char *msg)
{
	size_t	len = strlen(msg);

	for (int fd = 0; fd <= g_max; fd++)
		if (g_used[fd] && fd != except && FD_ISSET(fd, &g_wr))
			send(fd, msg, len, 0);
}

static void	add_client(void)
{
	char	msg[64];
	int		fd;

	fd = accept(g_listen, NULL, NULL);
	if (fd < 0)
		return ;
	if (fd >= FD_SETSIZE)
	{
		close(fd);
		return ;
	}
	g_used[fd] = 1;
	g_clients[fd].id = g_next_id++;
	g_clients[fd].buf = NULL;
	FD_SET(fd, &g_all);
	if (fd > g_max)
		g_max = fd;
	sprintf(msg, "server: client %d just arrived\n", g_clients[fd].id);
	broadcast(fd, msg);
}

static void	remove_client(int fd)
{
	char	msg[64];

	sprintf(msg, "server: client %d just left\n", g_clients[fd].id);
	broadcast(fd, msg);
	free(g_clients[fd].buf);
	g_clients[fd].buf = NULL;
	g_used[fd] = 0;
	FD_CLR(fd, &g_all);
	close(fd);
}

static void	read_client(int fd)
{
	char	recv_buf[4097];
	char	prefix[64];
	char	*line;
	char	*out;
	int		n;
	int		r;

	n = recv(fd, recv_buf, 4096, 0);
	if (n <= 0)
	{
		remove_client(fd);
		return ;
	}
	recv_buf[n] = 0;
	g_clients[fd].buf = str_join(g_clients[fd].buf, recv_buf);
	if (!g_clients[fd].buf)
		fatal();
	sprintf(prefix, "client %d: ", g_clients[fd].id);
	while ((r = extract_message(&g_clients[fd].buf, &line)) == 1)
	{
		out = malloc(strlen(prefix) + strlen(line) + 1);
		if (!out)
			fatal();
		strcpy(out, prefix);
		strcat(out, line);
		broadcast(fd, out);
		free(out);
		free(line);
	}
	if (r == -1)
		fatal();
}

int	main(int argc, char **argv)
{
	struct sockaddr_in	addr;

	if (argc != 2)
	{
		write(2, "Wrong number of arguments\n", 26);
		exit(1);
	}
	g_listen = socket(AF_INET, SOCK_STREAM, 0);
	if (g_listen < 0)
		fatal();
	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = htonl(2130706433);
	addr.sin_port = htons(atoi(argv[1]));
	if (bind(g_listen, (const struct sockaddr *)&addr, sizeof(addr)) != 0
		|| listen(g_listen, 128) != 0)
		fatal();
	FD_ZERO(&g_all);
	FD_SET(g_listen, &g_all);
	g_max = g_listen;
	while (1)
	{
		g_rd = g_all;
		g_wr = g_all;
		if (select(g_max + 1, &g_rd, &g_wr, NULL, NULL) < 0)
			continue ;
		for (int fd = 0; fd <= g_max; fd++)
		{
			if (!FD_ISSET(fd, &g_rd))
				continue ;
			if (fd == g_listen)
				add_client();
			else if (g_used[fd])
				read_client(fd);
		}
	}
}
