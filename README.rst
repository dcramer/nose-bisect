nose-bisect
===========

Inspired by Django's internal bisect tool, easily bisect your test suite and find test-on-test failures.

More importantly: Test FOO fails when run when test X, bisect will tell you what X is.

::

    nosetests --bisect=module:TestClass.failing_test

And get some sometimes-useful output::

    Bisecting against tests.integration.disqus.forums.api.endpoints.tests:ForumEndpointTest.test_list_users
    ├── Pass 1: Running 1410 test(s) in 2 chunks...
    │   ├── Chunk 1a: Running 780 tests
    │   │   └── Tests completed in 371.578s (failure found)
    │   ├── Chunk 1b: Running 631 tests
    │   │   └── Tests completed in 224.881s (failure found)
    │   └── Multiple sources of failure found (2 chunks)

(In our above case, our test suite is actually broken, so it's failing to find a way to bisect)