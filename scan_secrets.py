#!/usr/bin/env python3

import os.path
import os
import sys
import re
from collections import OrderedDict
import fnmatch

CWD = os.environ['PWD']

RSA_TOKENS = [
    '-----BEGIN RSA PRIVATE KEY-----',
    '-----END RSA PRIVATE KEY-----',
]
SKIP = [
    '@click.pass_obj',
    'a@b.c',
    'info@datakitchen.io',
    '127.0.0.1',
    '192.168.50.100',  # it's a vagrant local address, no worries
    'ghe.datakitchen.io',
    'cloud.datakitchen.io',
    'info@datakitchen.io',
    'github.com',
    'success@simulator.amazonses.com',
    'stackoverflow.com'
]

IGNORED = ['.gitignore', '.coveragerc', 'dk_logger.log']

SKIP_FILES = [
    '**/.git/**/*', '**/.git/*', '**/*.png', '**/*.pyc', '**/LICENSE.txt', '**/LICENSE',
    '**/setup.py', '**/README.md'
]

USER_PATTERNS = [
    re.compile(r'([a-zA-Z0-9\.]+@[a-zA-Z0-9]+.[a-zA-Z0-9\.]+)'),
    re.compile(
        r'[^_^\-](username|Username|USERNAME|User|user|USER)[^_^\-^,]([ ][=]?[ ]?)?(" *: *")?([a-zA-Z0-9\._\-@]+)'
    )
]

AWS_PATTERNS = [
    re.compile(r'([A-Z0-9]{20})'),
    re.compile(
        r'("|\')?(AWS|aws|Aws)?_?(SECRET|secret|Secret)?_?(ACCESS|access|Access)?_?(KEY|key|Key)("|\')?\s*(:|=>|=)\s*("|\')?[A-Za-z0-9/\+=]{40}("|\')?'  # noqa: E501
    ),
    re.compile(
        r'("|\')?(AWS|aws|Aws)?_?(ACCOUNT|account|Account)_?(ID|id|Id)?("|\')?\s*(:|=>|=)\s*("|\')?[0-9]{4}\-?[0-9]{4}\-?[0-9]{4}("|\')?'  # noqa: E501
    )
]

HOST_PATTERNS = [
    re.compile(r'([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'),
    re.compile(r'(http|https|ftp|scp|sftp)://([^/^\)^ ]+)'),
    #    re.compile(r'([a-zA-Z0-9\-_]+)\.([a-zA-Z0-9\-_]+)+\.([a-zA-Z0-9\-_]+)')
]
WELL_KNOWN_TOKENS = ['celgene', 'egalet', 'hemonc', 'crs']

PASSWORD_PATTERNS = [
    re.compile(
        r'[^_^\-](password|Password|PASSWORD|Pass|pass|PASS)[^_^\-^,]([ ][=]?[ ]?)?(" *: *")?([a-zA-Z0-9_\-.@]+)'
    )
]


def valid(item):
    v = not any([fnmatch.fnmatch(item, pattern) for pattern in SKIP_FILES])
    return v


class Issue:

    def __init__(self, path, line, error, message):
        self.path = path
        self.line = line
        self.error = error
        self.message = message

    def __str__(self):
        return '%s:%d:\033[31m%s\033[39m' % (self.path, self.line, self.message)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.path == other.path and \
            self.line == other.line and \
            self.message == other.message

    def __hash__(self):
        return hash(str(self.path) + str(self.line) + str(self.message))


def ignore(tokens, line, path, basepath, linenum, accepted_cases):
    if accepted_cases and path in accepted_cases and linenum in accepted_cases[path]:
        expression = accepted_cases[path][linenum]

        if expression == '*':
            return True
        else:
            return expression.search(line) is not None

    return any([token in SKIP for token in tokens])


def flatten(datalist):
    result = []

    for i in datalist:
        if isinstance(i, list) or isinstance(i, tuple):
            result += flatten(i)
        else:
            result.append(i)

    return result


def do_scan_regex(path, text, patterns, accepted_cases, basepath, msg_format):
    results = set()
    for i, line in enumerate(text):
        for regex in patterns:
            result = flatten(regex.findall(line))
            if len(result) > 0 and not ignore(result, line, path, basepath, i + 1, accepted_cases):
                results.add(Issue(path, i + 1, line.strip(), msg_format % line.strip()))

    return results


def scan_hosts(path, text, accepted_cases, basepath):
    return do_scan_regex(
        path, text, HOST_PATTERNS, accepted_cases, basepath,
        'Found potential hostname/IP address, line: %s'
    )


def scan_usernames(path, text, accepted_cases, basepath):
    return do_scan_regex(
        path, text, USER_PATTERNS, accepted_cases, basepath, 'Found potential username, line: %s'
    )


def scan_aws_credentials(path, text, accepted_cases, basepath):
    return do_scan_regex(
        path, text, AWS_PATTERNS, accepted_cases, basepath, 'Found AWS credential, line: %s'
    )


def scan_passwords(path, text, accepted_cases, basepath):
    return do_scan_regex(
        path, text, PASSWORD_PATTERNS, accepted_cases, basepath,
        'Found potential password, line: %s'
    )


def scan_well_known_tokens(path, text, accepted_cases, basepath):
    results = set()
    for i, line in enumerate(text):
        line = line.lower()
        for pattern in WELL_KNOWN_TOKENS:
            if pattern in line:
                results.add(
                    Issue(
                        path, i + 1, line.strip(),
                        'Found token "%s", line: %s' % (pattern, line.strip())
                    )
                )
    return results


def scan_key_files(path, text, accepted_cases, basepath):
    for item in text:
        if item.strip() in RSA_TOKENS:
            return set([Issue(path, 1, '*', 'Potential Key File')])
    return set()


def scan_file(path, accepted_cases, basepath):

    with open(path, 'r') as f:
        contents = f.readlines()

    scanners = [
        scan_usernames, scan_aws_credentials, scan_passwords, scan_key_files, scan_hosts,
        scan_well_known_tokens
    ]

    results = set()

    for scanner in scanners:
        results |= scanner(path, contents, accepted_cases, basepath)

    return results


def scan(path, accepted_cases, basepath):
    results = set()
    for item in os.listdir(path):

        fullpath = os.path.join(path, item)

        if valid(fullpath):
            if os.path.isdir(fullpath):
                results |= scan(fullpath, accepted_cases, basepath)
            else:
                results |= scan_file(fullpath, accepted_cases, basepath)

    return results


def group_by_path(issues):
    result = OrderedDict()

    for issue in issues:
        if issue.path not in result:
            result[issue.path] = set()
        result[issue.path].add(issue)

    return result


def scan_and_group(path, accepted_cases):
    results = scan(path, accepted_cases, path)
    return group_by_path(results)


def print_issues(results):
    for path, issues in results.items():
        issues = list(issues)
        issues.sort(key=lambda x: x.line)
        for issue in issues:
            if issue.error.strip() != '*':
                error = '.*%s.*' % issue.error\
                    .replace('(', r'\(')\
                    .replace(')', r'\)')\
                    .replace('[', r'\[')\
                    .replace(']', r'\]')\
                    .replace('.', r'\.')  # noqa: E231
            else:
                error = '*'
            print('%s,%d,%s' % (path, issue.line, error))


def parse_accepted_cases(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    results = {}

    for line in lines:
        # Ignore blank and comments
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        tokens = line.split(',')
        filepath = tokens[0]
        line = int(tokens[1])
        expr = ','.join(tokens[2:]).strip()

        cases = results.get(filepath, {})
        cases[line] = re.compile(expr) if expr != '*' else expr
        results[filepath] = cases

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('scan-secrets.py [base path] [accepted cases file, optional]')
        sys.exit(1)

    path = sys.argv[1]

    accepted_cases = None
    if len(sys.argv) == 3:
        accepted_cases = parse_accepted_cases(sys.argv[2])

    results = scan_and_group(path, accepted_cases)

    if len(results) > 0:
        print_issues(results)
        sys.exit(1)
