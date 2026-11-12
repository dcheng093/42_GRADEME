#include "mini_db.hpp"

#include <cerrno>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

static volatile sig_atomic_t	g_stop = 0;

static void	on_sigint(int)
{
	g_stop = 1;
}

// ── database ──
Database::Database(const std::string &path) : _path(path) {}

void	Database::load()
{
	std::ifstream	in(_path.c_str());
	std::string		key;
	std::string		value;

	while (in >> key >> value)
		_entries[key] = value;
}

bool	Database::save() const
{
	std::ofstream	out(_path.c_str(), std::ios::trunc);

	for (std::map<std::string, std::string>::const_iterator it = _entries.begin(); it != _entries.end(); ++it)
		out << it->first << ' ' << it->second << '\n';
	return (out.good());
}

std::string	Database::execute(const std::string &line)
{
	std::istringstream	in(line);
	std::string			cmd;
	std::string			key;
	std::string			value;
	std::string			extra;

	in >> cmd;
	if (cmd == "POST" && in >> key >> value && !(in >> extra))
	{
		_entries[key] = value;
		return ("0");
	}
	if (cmd == "GET" && in >> key && !(in >> extra))
	{
		std::map<std::string, std::string>::const_iterator it = _entries.find(key);
		return (it == _entries.end() ? "1" : "0 " + it->second);
	}
	if (cmd == "DELETE" && in >> key && !(in >> extra))
		return (_entries.erase(key) ? "0" : "1");
	return ("2");
}

// ── server ──
Server::Server(Database &db) : _listen(-1), _db(db) {}

Server::~Server()
{
	for (std::map<int, std::string>::iterator it = _pending.begin(); it != _pending.end(); ++it)
		close(it->first);
	if (_listen != -1)
		close(_listen);
}

bool	Server::start(int port)
{
	struct sockaddr_in	addr;
	int					yes = 1;

	_listen = socket(AF_INET, SOCK_STREAM, 0);
	if (_listen < 0)
		return (false);
	setsockopt(_listen, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
	std::memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	addr.sin_port = htons(port);
	if (bind(_listen, reinterpret_cast<struct sockaddr *>(&addr), sizeof(addr)) < 0)
		return (false);
	if (listen(_listen, 128) < 0)
		return (false);
	return (true);
}

void	Server::accept_client()
{
	int	fd = accept(_listen, NULL, NULL);

	if (fd >= 0 && fd < FD_SETSIZE)
		_pending[fd] = "";
	else if (fd >= 0)
		close(fd);
}

bool	Server::read_client(int fd)
{
	char		buf[4096];
	ssize_t		n = recv(fd, buf, sizeof(buf), 0);
	std::string	&pending = _pending[fd];
	std::string	reply;
	size_t		nl;

	if (n <= 0)
		return (false);
	pending.append(buf, n);
	while ((nl = pending.find('\n')) != std::string::npos)
	{
		reply += _db.execute(pending.substr(0, nl)) + "\n";
		pending.erase(0, nl + 1);
	}
	for (size_t sent = 0; sent < reply.size(); )
	{
		ssize_t k = send(fd, reply.data() + sent, reply.size() - sent, 0);
		if (k <= 0)
			return (false);
		sent += k;
	}
	return (true);
}

void	Server::run()
{
	fd_set	readable;
	int		max_fd;

	while (!g_stop)
	{
		FD_ZERO(&readable);
		FD_SET(_listen, &readable);
		max_fd = _listen;
		for (std::map<int, std::string>::iterator it = _pending.begin(); it != _pending.end(); ++it)
		{
			FD_SET(it->first, &readable);
			if (it->first > max_fd)
				max_fd = it->first;
		}
		if (select(max_fd + 1, &readable, NULL, NULL, NULL) < 0)
			continue ;  // EINTR: SIGINT arrived
		if (FD_ISSET(_listen, &readable))
			accept_client();
		for (int fd = 0; fd <= max_fd; fd++)
		{
			if (fd == _listen || !FD_ISSET(fd, &readable) || !_pending.count(fd))
				continue ;
			if (!read_client(fd))
			{
				close(fd);
				_pending.erase(fd);
			}
		}
	}
}

int	main(int argc, char **argv)
{
	struct sigaction	sa;

	if (argc != 3)
	{
		std::cerr << "usage: ./mini_db <port> <file>" << std::endl;
		return (1);
	}
	Database	db(argv[2]);
	db.load();
	Server		server(db);
	if (!server.start(std::atoi(argv[1])))
	{
		std::cerr << "Fatal error" << std::endl;
		return (1);
	}
	std::memset(&sa, 0, sizeof(sa));
	sa.sa_handler = on_sigint;
	sigemptyset(&sa.sa_mask);
	sigaction(SIGINT, &sa, NULL);
	std::cout << "ready" << std::endl;
	server.run();
	return (db.save() ? 0 : 1);
}
