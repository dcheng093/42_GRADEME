#include <stdio.h>
#include <stdbool.h>
#include <ctype.h>
#include <string.h>
#include <stdlib.h>

typedef struct	json {
	enum {
		MAP,
		INTEGER,
		STRING
	} type;
	union {
		struct {
			struct pair	*data;
			size_t		size;
		} map;
		int	integer;
		char	*string;
	};
}	json;

typedef struct	pair {
	char	*key;
	json	value;
}	pair;

void	free_json(json j);
int	argo(json *dst, FILE *stream);

int	peek(FILE *stream)
{
	int	c = getc(stream);
	ungetc(c, stream);
	return c;
}

void	unexpected(FILE *stream)
{
	if (peek(stream) != EOF)
		printf("unexpected token '%c'\n", peek(stream));
	else
		printf("unexpected end of input\n");
}

int	accept(FILE *stream, char c)
{
	if (peek(stream) == c)
	{
		(void)getc(stream);
		return 1;
	}
	return 0;
}

int	expect(FILE *stream, char c)
{
	if (accept(stream, c))
		return 1;
	unexpected(stream);
	return 0;
}

void	free_json(json j)
{
	switch (j.type)
	{
		case MAP:
			for (size_t i = 0; i < j.map.size; i++)
			{
				free(j.map.data[i].key);
				free_json(j.map.data[i].value);
			}
			free(j.map.data);
			break ;
		case STRING:
			free(j.string);
			break ;
		default:
			break ;
	}
}

void	serialize(json j)
{
	switch (j.type)
	{
		case INTEGER:
			printf("%d", j.integer);
			break ;
		case STRING:
			putchar('"');
			for (int i = 0; j.string[i]; i++)
			{
				if (j.string[i] == '\\' || j.string[i] == '"')
					putchar('\\');
				putchar(j.string[i]);
			}
			putchar('"');
			break ;
		case MAP:
			putchar('{');
			for (size_t i = 0; i < j.map.size; i++)
			{
				if (i != 0)
					putchar(',');
				serialize((json){.type = STRING, .string = j.map.data[i].key});
				putchar(':');
				serialize(j.map.data[i].value);
			}
			putchar('}');
			break ;
	}
}

static int	parse_value(json *dst, FILE *stream);

// "..." with only \\ and \" as escapes
static int	parse_string(char **out, FILE *stream)
{
	size_t	len = 0;
	size_t	cap = 16;
	char	*buf;
	char	*bigger;
	int		c;

	*out = NULL;
	if (!expect(stream, '"'))
		return (-1);
	buf = malloc(cap);
	if (!buf)
		return (-1);
	while (1)
	{
		c = getc(stream);
		if (c == EOF)
			return (free(buf), unexpected(stream), -1);
		if (c == '"')
			break ;
		if (c == '\\')
		{
			c = getc(stream);
			if (c == EOF)
				return (free(buf), unexpected(stream), -1);
			if (c != '\\' && c != '"')
			{
				ungetc(c, stream);
				return (free(buf), unexpected(stream), -1);
			}
		}
		if (len + 1 >= cap)
		{
			bigger = realloc(buf, cap * 2);
			if (!bigger)
				return (free(buf), -1);
			buf = bigger;
			cap *= 2;
		}
		buf[len++] = (char)c;
	}
	buf[len] = '\0';
	*out = buf;
	return (1);
}

static int	parse_integer(json *dst, FILE *stream)
{
	int	n;

	if (fscanf(stream, "%d", &n) != 1)
		return (unexpected(stream), -1);
	dst->type = INTEGER;
	dst->integer = n;
	return (1);
}

static int	parse_map(json *dst, FILE *stream)
{
	pair	*bigger;
	char	*key;

	dst->type = MAP;
	dst->map.data = NULL;
	dst->map.size = 0;
	if (!expect(stream, '{'))
		return (-1);
	if (accept(stream, '}'))
		return (1);
	while (1)
	{
		if (parse_string(&key, stream) != 1)
			return (-1);
		bigger = realloc(dst->map.data, sizeof(pair) * (dst->map.size + 1));
		if (!bigger)
			return (free(key), -1);
		dst->map.data = bigger;
		dst->map.data[dst->map.size].key = key;
		dst->map.data[dst->map.size].value.type = INTEGER;
		dst->map.size++;
		if (!expect(stream, ':'))
			return (-1);
		if (parse_value(&dst->map.data[dst->map.size - 1].value, stream) != 1)
			return (-1);
		if (accept(stream, '}'))
			return (1);
		if (!expect(stream, ','))
			return (-1);
	}
}

static int	parse_value(json *dst, FILE *stream)
{
	int	c = peek(stream);

	dst->type = INTEGER;  // always safe to free_json()
	if (c == '"')
	{
		dst->type = STRING;
		return (parse_string(&dst->string, stream));
	}
	if (c == '{')
		return (parse_map(dst, stream));
	if (isdigit(c) || c == '-')
		return (parse_integer(dst, stream));
	unexpected(stream);
	return (-1);
}

int	argo(json *dst, FILE *stream)
{
	dst->type = INTEGER;
	if (!stream)
		return (-1);
	return (parse_value(dst, stream));
}

int	main(int argc, char **argv)
{
	if (argc != 2)
		return 1;
	char *filename = argv[1];
	FILE *stream = fopen(filename, "r");
	json	file;
	if (argo(&file, stream) != 1)
	{
		free_json(file);
		return 1;
	}
	serialize(file);
	printf("\n");
}
