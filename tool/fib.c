#include <stdio.h>

int fib(int n) {
    if (n < 2 ) return n;
    return fib(n - 2) + fib(n - 1);
}
int main(int argc, const char* argv[]) {
    int n = 35;
    int f = fib(n);
    printf("fib(%d) = %d\n", n, f);
}