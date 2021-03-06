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
    result = subprocess.run(['cmake-build-debug/clox', test_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout.decode('utf-8')


def compare_to_expected(result, expected_file):
    with open(expected_file, 'r') as rf:
        test_output = rf.read()
        return test_output == result, test_output


def run_test(test_file, directory, fail_hard=False):
    print(f'Running: {test_file[len(directory):-4]} ... ', end='')
    interpreter = lox.Lox()

    if not os.path.exists(test_file + '.out'):
        print(red(f'missing test output!'))
        return False

    output = run_plox_test(interpreter, test_file)
    plox_state, plox_expct = compare_to_expected(output, test_file + '.out')

    c_output = run_clox_test(interpreter, test_file)
    if os.path.exists(test_file + '.cout'):
        clox_state, clox_expct = compare_to_expected(c_output, test_file + '.cout')
    else:
        clox_state, clox_expct = compare_to_expected(c_output, test_file + '.out')

    if plox_state and clox_state:
        print(green(f'success!'))
        return True

    if not plox_state or not clox_state:
        print(red(f'failed!'))

    if not plox_state:
        print('plox:')
        print(output)
        print('---')
        print('Expected:')
        print(plox_expct)
        print('---')

    if not clox_state:
        print('clox:')
        print(c_output)
        print('---')
        print('Expected:')
        print(clox_expct)
        print('---')

        # hex_output = [hex(ord(x))[2:] for x in output]
        # hex_c_output = [hex(ord(x))[2:] for x in c_output]
        #
        # for i, (a, b) in enumerate(zip(hex_output, hex_c_output)):
        #     if a != b:
        #         print(i, a, b)
        #
        # print(':'.join(hex_output))
        # print(':'.join(hex_c_output))

    if fail_hard:
        test_output_file = test_file + '.out'
        dump_output(test_output_file + '.pdump', output)
        dump_output(test_output_file + '.cdump', c_output)
    return False


def run_tests(directory, fail_hard=True, exclude=None):
    print(f'Running tests in {directory}')

    if directory in exclude:
        print('Skipping...\n')
        return 0, 0, []

    success_count = 0
    fail_count = 0
    failed_tests = []
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
                failed_tests.append(f)

            if not test_succeeded and fail_hard:
                return success_count, fail_count, failed_tests

    print('')
    for d in dirs:
        s, f, failed = run_tests(d, fail_hard, exclude)
        success_count += s
        fail_count += f
        failed_tests.extend(failed)
        if len(failed) > 0 and fail_hard:
            break

    return success_count, fail_count, failed_tests


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
    success, failed, failed_tests = run_tests(test_path, fail_hard=False, exclude=excludes)
    print(f'{success} test(s) succeeded and {failed} test(s) failed')

    #print("Overview of failed test(s):")
    #for test in failed_tests:
    #    print(test)
