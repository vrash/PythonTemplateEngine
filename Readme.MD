Readme.MD

Notes:
Written in python

How to run:
1. Install Python 3.0 and above if not installed already
2. Run templater.py with three arguments giving full file paths
eg. python templater.py /users/slartibartfast/abcd.template /users/slartibartfast/data.json /users/slartibartfast/output.html

**IMPORTANT**
Changes to be made to input template:
--------------------------------------
1.The template suggested is not scalable or extensible to large templates or other types of conditional statements or calls. Hence for conditionals please replace <*..*> with <%..%>.  Also to end a block of conditional or loop use end instead of endeach.
For example  in the given example replace
<* EACH arrayName itemName *> ... <* ENDEACH *> 
with 
<% each arrayName %> ... <% end %>

Modified template example is included
This way its much more extensible and you can write conditional blocks such as if..else or comparisons. 

2. Replace loop variables with the word "it" (for item) in the looping constructs as shown in the sample template. This is done for simplicity of code, and time crunch. 


TODO:
1. Write assertion test cases and benchmark with other engines - in progress
2. Take loop variables instead of supplying "it" variable
3. Extend this, MVC-fy it, include a lot more checks and host on github, since its a fast and loose templating engine, unlike some of the slower larger ones out there
4. Explore moving away from regexp altogether and do contextual matches, because well:http://stackoverflow.com/questions/1732348/regex-match-open-tags-except-xhtml-self-contained-tags
