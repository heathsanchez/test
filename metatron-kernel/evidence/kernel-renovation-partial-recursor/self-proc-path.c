#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

/* Container compatibility: resolve only this process's executable through
   its permitted /proc/self alias. All other readlink calls are unchanged. */
ssize_t readlink(const char *path, char *buf, size_t size) {
    ssize_t (*real_readlink)(const char *, char *, size_t) = dlsym(RTLD_NEXT, "readlink");
    char own_exe[64];
    snprintf(own_exe, sizeof own_exe, "/proc/%d/exe", (int)getpid());
    return real_readlink(strcmp(path, own_exe) == 0 ? "/proc/self/exe" : path, buf, size);
}
