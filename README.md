PythonTemplateEngine
====================

Notes:
-------

Written in python

How to run:
------------

1. Install Python 3.0 and above if not installed already

2. Run templater.py with three arguments giving full file paths
eg. python templater.py /users/slartibartfast/abcd.template /users/slartibartfast/data.json /users/slartibartfast/output.html


TODO:
--------
1. Write assertion test cases and benchmark with other engines - in progress

2. Take loop variables instead of supplying "it" variable

3. Extend this, MVC-fy it, include a lot more checks and host on github, since its a fast and loose templating engine, unlike some of the slower larger ones out there

4. Explore moving away from regexp altogether and do contextual matches, because well:

http://stackoverflow.com/questions/1732348/regex-match-open-tags-except-xhtml-self-contained-tags
