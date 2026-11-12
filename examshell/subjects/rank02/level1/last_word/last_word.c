#include <unistd.h>

int main(int ac, char *av[])
{
    int start;
    int end;
    int i = 0;
    if (ac == 2)
    {
        while (av[1][i])
            i++;
        i--;
        while ((av[1][i] >= 9 && av[1][i] <= 13) || (av[1][i] == 32))
            i--;
        end = i;
        while ((av[1][i]) && !((av[1][i] >= 9 && av[1][i] <= 13) || (av[1][i] == 32)))
            i--;
        start = i + 1;
        while (start <= end)
            write (1, &av[1][start++], 1);
    }
    write (1, "\n", 1);
}