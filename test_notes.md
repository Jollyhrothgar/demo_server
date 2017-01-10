# hard_func Tests
1. hard_func?args=[1,2,3]&arg1=23&arg2="tom"&default1='single_quoted'&default2=11.2&"mike"=10

* Fails, appears to be string parsing problem.

2. http://localhost:5002/execute/a_test_module.test_module/hard_func?args=[1,2,3]&arg1=%22dude%22&arg2=%22whereis%22&default1=%22mycar%22&default2=20&extra=%27hi%27&extra2=%27another%27 

* works - url should not have quotes around the keys of keyword arguments.
