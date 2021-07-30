-- account control

CREATE TYPE role_type AS ENUM (
  'GUEST',
  'NORMAL',
  'MANAGER'
);  -- 'MANAGER' > 'NORMAL'

CREATE TABLE account (
  id                SERIAL    PRIMARY KEY,
  username          VARCHAR   NOT NULL UNIQUE,
  pass_hash         VARCHAR   NOT NULL,
  nickname          VARCHAR   NOT NULL,
  real_name         VARCHAR   NOT NULL,
  role              role_type NOT NULL,  -- global role
  alternative_email VARCHAR,
  is_deleted        BOOLEAN   NOT NULL  DEFAULT false,
  is_4s_hash        BOOLEAN   NOT NULL  DEFAULT false
);

CREATE TABLE institute (
  id                SERIAL  PRIMARY KEY,
  abbreviated_name  VARCHAR NOT NULL  UNIQUE,
  full_name         VARCHAR NOT NULL  UNIQUE,
  email_domain      VARCHAR NOT NULL  UNIQUE,
  is_disabled       BOOLEAN NOT NULL  DEFAULT false
);

CREATE TABLE student_card (
  id            SERIAL  PRIMARY KEY,
  account_id    INTEGER NOT NULL  REFERENCES account(id),
  institute_id  INTEGER NOT NULL  REFERENCES institute(id),
  department    VARCHAR NOT NULL,
  student_id    VARCHAR NOT NULL,
  email         VARCHAR NOT NULL  UNIQUE,
  is_default    BOOLEAN NOT NULL  DEFAULT false,

  UNIQUE (institute_id, student_id)
);

CREATE TABLE email_verification (
  code          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  email         VARCHAR NOT NULL,
  account_id    INTEGER NOT NULL  REFERENCES account(id),
  institute_id  INTEGER           REFERENCES institute(id),
  department    VARCHAR,
  student_id    VARCHAR,
  is_consumed   BOOLEAN NOT NULL  DEFAULT false
);


-- Course management


CREATE TYPE course_type AS ENUM (
  'LESSON',
  'CONTEST'
);


CREATE TABLE course (
  id          SERIAL      PRIMARY KEY,
  name        VARCHAR     NOT NULL  UNIQUE,
  type        course_type NOT NULL,
  is_deleted  BOOLEAN     NOT NULL  DEFAULT false
);

CREATE TABLE class (
  id          SERIAL  PRIMARY KEY,
  name        VARCHAR NOT NULL,
  course_id   INTEGER NOT NULL  REFERENCES course(id),
  is_deleted  BOOLEAN NOT NULL  DEFAULT false,

  UNIQUE (course_id, name)
);

CREATE TABLE class_member (
  class_id  INTEGER   NOT NULL  REFERENCES class(id),
  member_id INTEGER   NOT NULL  REFERENCES account(id),
  role      role_type NOT NULL,

  PRIMARY KEY (class_id, member_id)
);

CREATE TABLE team (
  id          SERIAL  PRIMARY KEY,
  name        VARCHAR NOT NULL,
  class_id    INTEGER NOT NULL  REFERENCES class(id),
  label       VARCHAR NOT NULL,
  is_deleted  BOOLEAN NOT NULL  DEFAULT false,

  UNIQUE (class_id, name)
);

CREATE TABLE team_member (
  team_id   INTEGER   NOT NULL  REFERENCES team(id),
  member_id INTEGER   NOT NULL  REFERENCES account(id),
  role      role_type NOT NULL,

  PRIMARY KEY (team_id, member_id)
);

CREATE TABLE grade (
  id          SERIAL    PRIMARY KEY,
  receiver_id INTEGER   NOT NULL  REFERENCES account(id),
  grader_id   INTEGER   NOT NULL  REFERENCES account(id),
  class_id    INTEGER   NOT NULL  REFERENCES class(id),
  title       VARCHAR   NOT NULL,
  score       INTEGER,
  comment     TEXT,
  update_time TIMESTAMP NOT NULL,
  is_deleted  BOOLEAN   NOT NULL  DEFAULT false,

  UNIQUE (receiver_id, title)
);


-- Challenge-task management

CREATE TYPE challenge_type AS ENUM (
  'CONTEST',
  'HOMEWORK'
);

CREATE TYPE challenge_publicize_type AS ENUM (
  'START_TIME',
  'END_TIME'
);

CREATE TABLE challenge (
  id                SERIAL                      PRIMARY KEY,
  class_id          INTEGER                     NOT NULL  REFERENCES class(id),
  type              challenge_type              NOT NULL,
  publicize_type    challenge_publicize_type    NOT NULL,
  title             VARCHAR                     NOT NULL,
  setter_id         INTEGER                     NOT NULL  REFERENCES account(id),
  description       TEXT,
  start_time        TIMESTAMP                   NOT NULL,
  end_time          TIMESTAMP                   NOT NULL,
  is_deleted        BOOLEAN                     NOT NULL  DEFAULT false,

  UNIQUE (class_id, title)
);

CREATE TYPE task_selection_type AS ENUM (
  'LAST',
  'BEST'
);


-- Problem management


CREATE TABLE problem (
  id              SERIAL              PRIMARY KEY,
  challenge_id    INTEGER             NOT NULL  REFERENCES challenge(id),
  challenge_label VARCHAR             NOT NULL,  -- 題號：1 2 3 or 2-a or 3-1 or A B C
  selection_type  task_selection_type NOT NULL,
  title           VARCHAR             NOT NULL  UNIQUE,
  setter_id       INTEGER             NOT NULL  REFERENCES account(id),
  full_score      INTEGER             NOT NULL,
  description     TEXT,
  source          TEXT,
  hint            TEXT,
  is_deleted      BOOLEAN             NOT NULL  DEFAULT false
);

CREATE TABLE testcase (
  id            SERIAL  PRIMARY KEY,
  problem_id    INTEGER NOT NULL  REFERENCES problem(id),
  is_sample     BOOLEAN NOT NULL,
  score         INTEGER NOT NULL, -- 保留設定扣分測資的空間
  input_file    VARCHAR,
  output_file   VARCHAR,
  time_limit    INTEGER NOT NULL, -- ms
  memory_limit  INTEGER NOT NULL, -- kb
  is_disabled   BOOLEAN NOT NULL  DEFAULT false,
  is_deleted    BOOLEAN NOT NULL  DEFAULT false
);


-- submission management

CREATE TABLE submission_language (
  id            SERIAL  PRIMARY KEY,
  name          VARCHAR NOT NULL,
  version       VARCHAR NOT NULL,
  is_disabled   BOOLEAN NOT NULL  DEFAULT false,

  UNIQUE (name, version)
);

CREATE TABLE submission (
  id              SERIAL    PRIMARY KEY,
  account_id      INTEGER   NOT NULL  REFERENCES account(id),
  problem_id      INTEGER   NOT NULL  REFERENCES problem(id),
  language_id     INTEGER   NOT NULL  REFERENCES submission_language(id),
  content_file    VARCHAR   NOT NULL,
  content_length  INTEGER   NOT NULL,
  submit_time     TIMESTAMP NOT NULL
);

CREATE TYPE judgment_status_type AS ENUM (
  'WAITING FOR JUDGE',
  'JUDGING',
  'ACCEPTED',
  'WRONG ANSWER',
  'MEMORY LIMIT EXCEED',
  'TIME LIMIT EXCEED',
  'RUNTIME ERROR',
  'COMPILE ERROR',
  'OTHER - CONTACT STAFF',
  'RESTRICTED FUNCTION',
  'SYSTEM ERROR'
);  -- 'ACCEPTED' < 'WRONG ANSWER'

-- rejudge => one submission many judgement

CREATE TABLE judgment (
  id            SERIAL                PRIMARY KEY,
  submission_id INTEGER               NOT NULL  REFERENCES submission(id),
  status        judgment_status_type  NOT NULL,
  total_time    INTEGER               NOT NULL,
  max_memory    INTEGER               NOT NULL,
  score         INTEGER               NOT NULL,  -- 保留設定扣分測資的空間
  judge_time    TIMESTAMP             NOT NULL
);

CREATE TABLE judge_case (
  judgment_id INTEGER               NOT NULL REFERENCES judgment(id),
  testcase_id INTEGER               NOT NULL REFERENCES testcase(id),
  status      judgment_status_type  NOT NULL,
  time_lapse  INTEGER               NOT NULL,
  peak_memory INTEGER               NOT NULL,
  score       INTEGER               NOT NULL,  -- 保留設定扣分測資的空間

  PRIMARY KEY (judgment_id, testcase_id)
);


-- Peer management

CREATE TABLE peer_review (
  id                SERIAL    PRIMARY KEY,
  challenge_id      INTEGER   NOT NULL  REFERENCES challenge(id),
  challenge_label   VARCHAR   NOT NULL,  -- 題號：1 2 3 or 2-a or 3-1 or A B C
  target_problem_id INTEGER   NOT NULL  REFERENCES problem(id),
  setter_id         INTEGER   NOT NULL  REFERENCES account(id),
  description       TEXT      NOT NULL,
  min_score         INTEGER   NOT NULL,
  max_score         INTEGER   NOT NULL,
  max_review_count  INTEGER   NOT NULL,  -- 一個人最多改幾份
  start_time        TIMESTAMP NOT NULL,
  end_time          TIMESTAMP NOT NULL,
  is_deleted        BOOLEAN   NOT NULL  DEFAULT false
);

/* every receiver one record -> 要改的時候 edit record, add grader -> 改完 edit record, add comment
   when every receiver one record all reviewed -> every receiver add one new record */

CREATE TABLE peer_review_record (
  id              SERIAL    PRIMARY KEY,
  peer_review_id  INTEGER   NOT NULL  REFERENCES peer_review(id),
  grader_id       INTEGER   NOT NULL  REFERENCES account(id),
  receiver_id     INTEGER   NOT NULL  REFERENCES account(id),
  submission_id   INTEGER   NOT NULL  REFERENCES submission(id),
  -- 因為分配的同時就會 create record，所以下面是 NULLABLE (批改完才會填入)
  score           INTEGER,
  comment         TEXT,
  submit_time     TIMESTAMP,

  UNIQUE (peer_review_id, grader_id, submission_id)
);


-- System

CREATE TABLE announcement (
  id          SERIAL    PRIMARY KEY,
  title       VARCHAR   NOT NULL,
  content     TEXT      NOT NULL,
  author_id   INTEGER   NOT NULL  REFERENCES account(id),
  post_time   TIMESTAMP NOT NULL, -- 排程貼文
  expire_time TIMESTAMP NOT NULL, -- 自動下架
  is_deleted  BOOLEAN   NOT NULL  DEFAULT false
);

CREATE TABLE access_log (
  id              BIGSERIAL PRIMARY KEY,
  access_time     TIMESTAMP NOT NULL,
  request_method  VARCHAR   NOT NULL, -- Longest is `CONNECT` -> 7
  resource_path   VARCHAR   NOT NULL,
  ip              VARCHAR   NOT NULL, -- Linux `INET6_ADDRSTRLEN = 48` -> 47 + terminating NULL
  account_id      INTEGER             REFERENCES account(id)
);
