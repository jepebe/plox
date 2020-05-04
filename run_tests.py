import os
import io
import subprocess
import sys
from contextlib import redirect_stdout

import plox.lox as lox


def red(text):
    return color(text, 1)


def color(text, value=0):
    return '\u001b[38;5;%im%s\u001b[0m' % (value, text)


def green(text):
    return color(text, 2)


def yellow(text):
    return color(text, 226)


def dump_output(path, output):
    print(f'creating test output for {path}')
    with open(path, 'w') as wf:
        wf.write(output)


def list_directory(directory):
    items = sorted(os.listdir(directory))
    items = [f'{directory}{item}' for item in items]
    files = [item for item in items if os.path.isfile(item)]
    dirs = [item + '/' for item in items if os.path.isdir(item)]
    return dirs, files


def run_plox_test(interpreter, test_file):
    with open(test_file, 'r') as lf:
        data = lf.read()
    with io.StringIO() as buf, redirect_stdout(buf):
        try:
            interpreter.run(data)
        except RecursionError as e:
            # Handle an exception not handled by Plox
            print('RecursionError: maximum recursion depth exceeded')
        output = buf.getvalue()
    return output


def run_clox_test(interpreter, test_file):
    result = subprocess.run(['cmake-build-debug/clox', test_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode('utf-8')


def run_test(test_file, directory, fail_hard=False):
    print(f'Running: {test_file[len(directory):-4]} ... ', end='')
    interpreter = lox.Lox()

    output = run_plox_test(interpreter, test_file)
    c_output = run_clox_test(interpreter, test_file)

    if output != c_output:
        print(red(f'failed! [plox != clox]'))
        print('plox:')
        print(output)
        print('clox:')
        print(c_output)
        return False

    test_output_file = test_file + '.out'
    if not os.path.exists(test_output_file):
        print(red(f'missing test output'))
        return False
    else:
        with open(test_output_file, 'r') as rf:
            test_output = rf.read()
            if test_output != output:
                print(red(f'failed!'))
                print('Expected:')
                print(test_output)
                print('Got:')
                print(output)
                if fail_hard:
                    dump_output(test_output_file + '.dump', output)
                return False
            else:
                print(green(f'succeeded!'))
                return True


def run_tests(directory, fail_hard=True, exclude=None):
    print(f'Running tests in {directory}')

    if directory in exclude:
        print('Skipping...\n')
        return 0, 0, False

    success_count = 0
    fail_count = 0
    dirs, files = list_directory(directory)

    for f in files:
        if f in exclude:
            print(f'Skipped: {f[len(directory):-4]}')
            continue

        if f.endswith('.lox'):
            test_succeeded = run_test(f, directory, fail_hard)
            if test_succeeded:
                success_count += 1
            else:
                fail_count += 1

            if not test_succeeded and fail_hard:
                return success_count, fail_count, True

    print('')
    for d in dirs:
        s, f, failed = run_tests(d, fail_hard, exclude)
        success_count += s
        fail_count += f
        if failed:
            return success_count, fail_count, True
    return success_count, fail_count, False


if __name__ == '__main__':
    test_path = 'test/'
    if len(sys.argv) > 2:
        print('Usage: run_tests [directory]')
        sys.exit(13)
    elif len(sys.argv) == 2:
        test_path = sys.argv[1]
        if not test_path.endswith('/'):
            test_path += '/'

    excludes = ['test/benchmark/']
    success, failed, _ = run_tests(test_path, fail_hard=False, exclude=excludes)
    print(f'{success} test(s) succeeded and {failed} test(s) failed')
