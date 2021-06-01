-- System

DROP TABLE IF EXISTS access_log;

DROP TABLE IF EXISTS announcement;


-- Peer management

DROP TABLE IF EXISTS peer_review_record;

DROP TABLE IF EXISTS peer_review;


-- Score

DROP TABLE IF EXISTS grade;


-- submission management

DROP TABLE IF EXISTS judgment_testcase_result;

DROP TABLE IF EXISTS judgment;

DROP TYPE IF EXISTS judgment_status_type;

DROP TABLE IF EXISTS submission;

DROP TABLE IF EXISTS submission_language;


-- Challenge-problem management

DROP TABLE IF EXISTS challenge_problem;

DROP TABLE IF EXISTS testcase;

DROP TABLE IF EXISTS problem;

DROP TYPE IF EXISTS problem_type;

DROP TABLE IF EXISTS challenge;

DROP TABLE IF EXISTS challenge_type;


-- Course management

DROP TABLE IF EXISTS team_member;

DROP TABLE IF EXISTS team;

DROP TABLE IF EXISTS class_member;

DROP TABLE IF EXISTS class;

DROP TABLE IF EXISTS course_member;

DROP TABLE IF EXISTS course;

DROP TYPE IF EXISTS course_type;


-- account control

DROP TABLE IF EXISTS email_verification;

DROP TABLE IF EXISTS student_card;

DROP TABLE IF EXISTS account;

DROP TABLE IF EXISTS institute;

DROP TYPE IF EXISTS role_type;
