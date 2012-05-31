"""
nose_bisect.plugin
~~~~~~~~~~~~~~~~~~

:copyright: 2012 DISQUS.
:license: Apache 2.0
"""

from __future__ import absolute_import

import itertools
import sys
import time
import unittest

from subprocess import Popen, PIPE
from nose.plugins.base import Plugin

from . import colors


class _EmptyClass(object):
    pass

stdout = sys.stdout
stderr = sys.stderr


def split_test_groups(test_labels, num=2):
    from collections import defaultdict

    grouped_labels = defaultdict(set)
    for label in test_labels:
        grouped_labels[label.rsplit('.', 1)[0]].add(label)

    return grouped_labels


def chunk_tests_from_groups(grouped_labels, bisect_label, num=2):
    """
    Split tests in ``num`` pieces.
    """
    chunks = [set() for i in xrange(num)]
    for n, group in enumerate(sorted(grouped_labels.itervalues())):
        chunks[n % num].update(group)

    chunks = map(list, chunks)
    for chunk in chunks:
        if bisect_label in chunk:
            chunk.remove(bisect_label)

    chunks = map(list, chunks)
    # ensure test label is at the **end** as state changes usually
    # happen before this test is run
    for chunk in chunks:
        chunk.append(bisect_label)

    return chunks


def make_bisect_runner(parent, bisect_label):
    if not colors.supports_color():
        colorize = lambda x, *a, **k: x
    else:
        colorize = colors.colorize

    class BisectTestRunner(parent.__class__):
        """
        Based on Django 1.3's bisect_tests, recursively splits all tests that are discovered
        into a bisect grid, grouped by their parent TestCase.
        """
        # TODO: potentially break things down further than class level based on whats happening
        # TODO: the way we determine "stop" might need some improvement
        def run(self, test):
            # find all test_labels grouped by base class
            test_labels = []
            context_list = list(test._tests)
            while context_list:
                context = context_list.pop()
                if isinstance(context, unittest.TestCase):
                    test = context.test
                    test_labels.append('%s:%s.%s' % (test.__class__.__module__, test.__class__.__name__,
                                                     test._testMethodName))
                else:
                    context_list.extend(context)

            result = self._makeResult()

            subprocess_args = [sys.executable, sys.argv[0]] + [x for x in sys.argv[1:] if (x.startswith('-') and not x.startswith('--bisect'))]

            iteration = 0
            split = 2
            stderr = []

            print >> stdout, colorize('')
            print >> stdout, "Bisecting against", colorize(bisect_label, opts=('underscore',))

            while True:
                iteration += 1
                print >> stdout, '├── Pass %s: Running %d test(s) in %d chunks...' % (colorize(str(iteration), opts=('bold',)), len(test_labels), split)

                grouped_labels = split_test_groups(test_labels, split)
                chunks = chunk_tests_from_groups(grouped_labels, bisect_label, split)

                if len(grouped_labels) == 2:  # we're down to the final two test cases
                    print >> stdout, ''
                    print >> stdout, "└── Failure found!"
                    print >> stdout, ''
                    for chunk in chunks:
                        print >> stdout, ' '.join(itertools.imap(str, chunk))
                    print >> stdout, ''
                    print >> stdout, 'Output from final run:'
                    print >> stdout, ''
                    print >> stdout, '\n'.join(stderr)
                    sys.exit(1)

                retcodes = []
                stderr = []

                for n, chunk in itertools.izip(xrange(97, 97 + split), chunks):
                    print >> stdout, '│   ├── Chunk %s: Running %d tests' % (
                        colorize('%s%s' % (iteration, chr(n)), opts=('bold',)), len(chunk))
                    start = time.time()
                    proc = Popen(subprocess_args + chunk, stdout=PIPE, stderr=PIPE)
                    stderr.append(proc.communicate()[1])
                    total = (time.time() - start)
                    retcodes.append(proc.returncode)
                    print >> stdout, '│   │   └── Tests completed in %.3fs' % (total,),
                    if proc.returncode:
                        print >> stdout, colorize('(failure found)', fg='red')
                    else:
                        print >> stdout, ''

                if sum(retcodes) == 1:
                    idx = retcodes.index(1)
                    test_labels = chunks[idx]
                    split = 2
                    print >> stdout, '│   └── Problem found in chunk %s.' % (chr(65 + idx),)

                elif sum(retcodes) == 0:
                    split = split * 2
                    if split > 8:
                        print >> stdout, "│   └── Unable to find a failure in combination with target"
                        sys.exit(0)
                    print >> stdout, "│   └── No source of failure found, splitting and reordering test suite in %d chunks..." % (split,)

                else:
                    print >> stdout, "│   └── Multiple sources of failure found (%d chunks)" % sum(retcodes)
                    print >> stdout, ''
                    print >> stdout, "Test labels were:"
                    for chunk in chunks:
                        print >> stdout, ' '.join(itertools.imap(str, chunk))
                    print >> stdout, ''
                    print >> stdout, 'Output from final run:'
                    print >> stdout, ''
                    print >> stdout, '\n'.join(stderr)
                    print >> stdout, ''
                    print >> stdout, "It's likely that your test is just broken :-)"
                    sys.exit(1)

            # TODO: return a real result
            sys.exit(0)
            return result

    inst = _EmptyClass()
    inst.__class__ = BisectTestRunner
    inst.__dict__.update(parent.__dict__)
    return inst


class BisectTests(Plugin):
    score = -sys.maxint

    def options(self, parser, env):
        parser.add_option("--bisect", dest="bisect_label", default=False)

    def configure(self, options, config):
        self.enabled = bool(options.bisect_label)
        self.bisect_label = options.bisect_label

    def prepareTestRunner(self, test):
        return make_bisect_runner(test, self.bisect_label)
