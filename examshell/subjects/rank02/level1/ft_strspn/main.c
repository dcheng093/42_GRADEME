#include <stdio.h>
size_t	ft_strspn(const char *s, const char *accept);

int main(int argc, char **argv)
{
    if (argc == 3)
        printf("ft_strspn(\"%s\", \"%s\") = %zu\n", argv[1], argv[2], ft_strspn(argv[1], argv[2]));
    return (0);
}
