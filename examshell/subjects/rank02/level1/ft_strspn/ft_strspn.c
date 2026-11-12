#include <stddef.h>

size_t	ft_strspn(const char *s, const char *accept)
{
	size_t	n;
	int		j;

	n = 0;
	while (s[n])
	{
		j = 0;
		while (accept[j] && accept[j] != s[n])
			j++;
		if (!accept[j])
			break ;
		n++;
	}
	return (n);
}
