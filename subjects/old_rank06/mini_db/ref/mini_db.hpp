#ifndef MINI_DB_HPP
#define MINI_DB_HPP

#include <map>
#include <string>

class Database
{
	std::map<std::string, std::string>	_entries;
	std::string							_path;

public:
	explicit Database(const std::string &path);

	void		load();
	bool		save() const;
	std::string	execute(const std::string &line);
};

class Server
{
	int									_listen;
	Database							&_db;
	std::map<int, std::string>			_pending;  // per client: bytes after the last '\n'

	void	accept_client();
	bool	read_client(int fd);

public:
	Server(Database &db);
	~Server();

	bool	start(int port);
	void	run();
};

#endif
