// LD_PRELOAD shim: read() on stdin returns 1 to 7 bytes at a time, the way
// the exam's "custom read function" fills your buffer unevenly
#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>

static ssize_t (*real_read)(int, void *, size_t);
static unsigned long state = 4242;

ssize_t	read(int fd, void *buf, size_t count)
{
	size_t	n;

	if (!real_read)
		real_read = (ssize_t (*)(int, void *, size_t))dlsym(RTLD_NEXT, "read");
	if (fd == 0 && count > 1)
	{
		state = state * 6364136223846793005UL + 1442695040888963407UL;
		n = 1 + (state >> 33) % 7;
		if (n < count)
			count = n;
	}
	return (real_read(fd, buf, count));
}
