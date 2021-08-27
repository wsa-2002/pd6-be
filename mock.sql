INSERT INTO account VALUES (1, 'admin', '$argon2id$v=19$m=102400,t=2,p=8$gbA2Ziyl9H5vLWXMeQ/hvA$oEjG4MX+m9yyezM42ialUg', 'admin', 'admin', 'MANAGER', 'test@gmail.com', false, false); -- password: admin

INSERT INTO account VALUES (2, 'student1', '$argon2id$v=19$m=102400,t=2,p=8$57zXOifEOKfUuheCMOZ8jw$AtMnhV+bGtWrLepNkXK0Zw', 'student1', 'student1', 'NORMAL', 'student1@gmail.com', false, false); --password: student1

INSERT INTO institute VALUES (1, 'NTU', 'National Taiwan University', 'ntu.edu.tw', true);

INSERT INTO institute VALUES (2, 'NTNU', 'National Taiwan Normal University', 'ntnu.edu.tw', true);

INSERT INTO student_card VALUES (1, 2, 1, 'IM', 'B10705001', 'B10705001@ntu.edu.tw', true);

INSERT INTO student_card VALUES (2, 2, 1, 'IM', 'R10705001', 'R10705001@ntu.edu.tw', false);

INSERT INTO course VALUES (1, 'PBC', 'LESSON', false);

INSERT INTO course VALUES (2, 'PD', 'LESSON', false);

INSERT INTO course VALUES (3, 'DSAP', 'LESSON', false);

INSERT INTO course VALUES (4, 'PDAO', 'CONTEST', false);

INSERT INTO class VALUES (1, '109-2', 1, false);

INSERT INTO class VALUES (2, '109-2', 2, false);

INSERT INTO class VALUES (3, '109-2', 3, false);

INSERT INTO class VALUES (4, '109-2', 4, false);

INSERT INTO class_member VALUES (1, 1, 'MANAGER');

INSERT INTO class_member VALUES (1, 2, 'NORMAL');

INSERT INTO class_member VALUES (2, 1, 'MANAGER');

INSERT INTO class_member VALUES (2, 2, 'NORMAL');

INSERT INTO class_member VALUES (3, 1, 'MANAGER');

INSERT INTO class_member VALUES (3, 2, 'NORMAL');

INSERT INTO class_member VALUES (4, 1, 'MANAGER');

INSERT INTO class_member VALUES (4, 2, 'NORMAL');

INSERT INTO access_log (access_time, request_method, resource_path, ip, account_id) VALUES ('2020-01-01 00:00:00', 'get', '/account', 'random_ip', 1);

INSERT INTO access_log (access_time, request_method, resource_path, ip, account_id) VALUES ('2020-01-01 00:00:00', 'get', '/account', 'random_ip', 1);

INSERT INTO announcement VALUES (1, 'title', 'content', 1, '2020-01-01 00:00:00', '2050-01-01 00:00:00', false);

INSERT INTO announcement VALUES (2, 'title2', 'content2', 1, '2020-01-02 00:00:00', '2029-01-01 00:00:00', false);

INSERT INTO submission_language VALUES (1, 'python', '3.9', false);

INSERT INTO submission_language VALUES (2, 'c++', '2.7.1', false);

