-- S3-file management

DROP TABLE IF EXISTS s3_file;


-- System

DROP TABLE IF EXISTS access_log;

DROP TABLE IF EXISTS announcement;


-- Peer management

DROP TABLE IF EXISTS peer_review_record;

DROP TABLE IF EXISTS peer_review;


-- submission management

DROP TABLE IF EXISTS judge_case;

DROP TABLE IF EXISTS judgment;

DROP TYPE IF EXISTS judgment_status_type;

DROP TABLE IF EXISTS submission;

DROP TABLE IF EXISTS submission_language;

DROP TABLE IF EXISTS testcase;

DROP TABLE IF EXISTS problem;


-- Challenge-task management

DROP TYPE IF EXISTS task_selection_type;

DROP TABLE IF EXISTS challenge;

DROP TYPE IF EXISTS challenge_type;


-- Course management

DROP TABLE IF EXISTS grade;

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

DROP TABLE IF EXISTS institute;

DROP TABLE IF EXISTS account;

DROP TYPE IF EXISTS role_type;
