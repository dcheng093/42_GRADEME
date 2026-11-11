// one ft_scanf scenario per argv[1], reading stdin; prints the return value
// and what was stored (variables start at 0 / '?' / "")
#include <stdio.h>
#include <stdlib.h>

int	ft_scanf(const char *format, ...);

int	main(int argc, char **argv)
{
	int		a = 0, b = 0, ret;
	char	c1 = '?', c2 = '?', c3 = '?';
	char	s1[256] = "", s2[256] = "";

	if (argc != 2)
		return (1);
	switch (atoi(argv[1]))
	{
		case 0: ret = ft_scanf("%d", &a); printf("\"%%d\" -> %d | %d\n", ret, a); break;
		case 1: ret = ft_scanf("%d %d", &a, &b); printf("\"%%d %%d\" -> %d | %d %d\n", ret, a, b); break;
		case 2: ret = ft_scanf("%s", s1); printf("\"%%s\" -> %d | [%s]\n", ret, s1); break;
		case 3: ret = ft_scanf("%c", &c1); printf("\"%%c\" -> %d | [%c]\n", ret, c1); break;
		case 4: ret = ft_scanf("%c%c%c", &c1, &c2, &c3); printf("\"%%c%%c%%c\" -> %d | [%c%c%c]\n", ret, c1, c2, c3); break;
		case 5: ret = ft_scanf(" %c", &c1); printf("\" %%c\" -> %d | [%c]\n", ret, c1); break;
		case 6: ret = ft_scanf("%d%s%c", &a, s1, &c1); printf("\"%%d%%s%%c\" -> %d | %d [%s] [%c]\n", ret, a, s1, c1); break;
		case 7: ret = ft_scanf("abc %d", &a); printf("\"abc %%d\" -> %d | %d\n", ret, a); break;
		case 8: ret = ft_scanf("%d,%d", &a, &b); printf("\"%%d,%%d\" -> %d | %d %d\n", ret, a, b); break;
		case 9: ret = ft_scanf("%s %s %d", s1, s2, &a); printf("\"%%s %%s %%d\" -> %d | [%s] [%s] %d\n", ret, s1, s2, a); break;
		case 10:
			while ((ret = ft_scanf("%d", &a)) == 1)
				printf("\"%%d\" -> 1 | %d\n", a);
			printf("\"%%d\" -> %d (stop)\n", ret);
			break;
		case 11: ret = ft_scanf("%s%c", s1, &c1); printf("\"%%s%%c\" -> %d | [%s] [%d]\n", ret, s1, c1); break;
		case 12:
			ret = ft_scanf("%d", &a);
			printf("first \"%%d\" -> %d | %d\n", ret, a);
			ret = ft_scanf("%s", s1);
			printf("then \"%%s\" -> %d | [%s]\n", ret, s1);
			break;
		default: return (1);
	}
	return (0);
}
