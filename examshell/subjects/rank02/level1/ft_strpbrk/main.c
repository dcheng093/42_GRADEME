#include <stdio.h>
char	*ft_strpbrk(const char *s1, const char *s2);

int main(int argc, char **argv)
{
    char *found;

    if (argc == 3)
    {
        found = ft_strpbrk(argv[1], argv[2]);
        if (found)
            printf("ft_strpbrk(\"%s\", \"%s\") = s1 + %ld (\"%s\")\n", argv[1], argv[2], (long)(found - argv[1]), found);
        else
            printf("ft_strpbrk(\"%s\", \"%s\") = NULL\n", argv[1], argv[2]);
    }
    return (0);
}
