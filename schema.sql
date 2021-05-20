-- account control

CREATE TYPE role_type AS ENUM (
  'GUEST',
  'NORMAL',
  'MANAGER'
);  -- 'MANAGER' > 'NORMAL'

CREATE TABLE institute (
  id            SERIAL  PRIMARY KEY,
  name          VARCHAR NOT NULL  UNIQUE,
  email_domain  VARCHAR NOT NULL  UNIQUE,
  is_enabled    BOOLEAN NOT NULL  DEFAULT false
);

CREATE TABLE account (
  id                SERIAL    PRIMARY KEY,
  name              VARCHAR   NOT NULL,
  pass_hash         VARCHAR   NOT NULL,
  nickname          VARCHAR   NOT NULL,
  real_name         VARCHAR   NOT NULL,
  role              role_type NOT NULL,  -- global role
  alternative_email VARCHAR,
  is_enabled        BOOLEAN   NOT NULL  DEFAULT false
);

CREATE TABLE student_card (
  id            SERIAL  PRIMARY KEY,
  account_id    INTEGER NOT NULL  REFERENCES account(id),
  institute_id  INTEGER NOT NULL  REFERENCES institute(id),
  department    VARCHAR NOT NULL,
  student_id    VARCHAR NOT NULL  UNIQUE,  -- UNIQUE for functional safety
  email         VARCHAR NOT NULL,
  is_enabled    BOOLEAN NOT NULL  DEFAULT false,

  UNIQUE (institute_id, student_id)
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
  is_enabled  BOOLEAN     NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN     NOT NULL  DEFAULT true
);

-- 好像沒屁用

CREATE TABLE course_member (
  course_id INTEGER   NOT NULL  REFERENCES course(id),
  member_id INTEGER   NOT NULL  REFERENCES account(id),
  role      role_type NOT NULL,

  PRIMARY KEY (course_id, member_id)
);

CREATE TABLE class (
  id          SERIAL  PRIMARY KEY,
  name        VARCHAR NOT NULL,
  course_id   INTEGER NOT NULL  REFERENCES course(id),
  is_enabled  BOOLEAN NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN NOT NULL  DEFAULT true,

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
  is_enabled  BOOLEAN NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN NOT NULL  DEFAULT true,

  UNIQUE (class_id, name)
);

CREATE TABLE team_member (
  team_id   INTEGER   NOT NULL  REFERENCES team(id),
  member_id INTEGER   NOT NULL  REFERENCES account(id),
  role      role_type NOT NULL,

  PRIMARY KEY (team_id, member_id)
);


-- Challenge-problem management

CREATE TABLE challenge_type (
  id    SERIAL  PRIMARY KEY,
  name  VARCHAR NOT NULL  UNIQUE
);

CREATE TABLE challenge (
  id          SERIAL    PRIMARY KEY,
  class_id    INTEGER   NOT NULL  REFERENCES class(id),
  type_id     INTEGER   NOT NULL  REFERENCES challenge_type(id),
  name        VARCHAR   NOT NULL,
  setter_id   INTEGER   NOT NULL  REFERENCES account(id),
  description TEXT,
  start_time  TIMESTAMP NOT NULL,
  end_time    TIMESTAMP NOT NULL,
  is_enabled  BOOLEAN   NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN   NOT NULL  DEFAULT true,

  UNIQUE (class_id, name)
);

CREATE TYPE problem_type AS ENUM (
  'JUDGE',
  'OPTIONS',
  'FILE',
  'PEER',
  'PROJECT',
  'SPECIAL'
);

CREATE TABLE problem (
  id          SERIAL        PRIMARY KEY,
  type_id     problem_type  NOT NULL,
  name        VARCHAR       NOT NULL  UNIQUE,
  setter_id   INTEGER       NOT NULL  REFERENCES account(id),
  full_score  INTEGER       NOT NULL,
  description TEXT,
  source      TEXT,
  hint        TEXT,
  is_enabled  BOOLEAN       NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN       NOT NULL  DEFAULT true
);

CREATE TABLE testdata (
  id            SERIAL  PRIMARY KEY,
  problem_id    INTEGER NOT NULL  REFERENCES problem(id),
  is_sample     BOOLEAN NOT NULL,
  score         INTEGER NOT NULL, -- 保留設定扣分測資的空間
  input_file    VARCHAR,
  ouptut_file   VARCHAR,
  time_limit    INTEGER, -- ms
  memory_limit  INTEGER, -- kb
  is_enabled    BOOLEAN NOT NULL  DEFAULT false,
  is_hidden     BOOLEAN NOT NULL  DEFAULT true
);

CREATE TABLE challenge_problem (
  challenge_id  INTEGER NOT NULL  REFERENCES challenge(id),
  problem_id    INTEGER NOT NULL  REFERENCES problem(id),

  PRIMARY KEY (challenge_id, problem_id)
);


-- submission management

CREATE TABLE submission_language (
  id      SERIAL  PRIMARY KEY,
  name    VARCHAR NOT NULL,
  version VARCHAR NOT NULL,

  UNIQUE (name, version)
);

CREATE TABLE submission (
  id              SERIAL    PRIMARY KEY,
  account_id      INTEGER   NOT NULL  REFERENCES account(id),
  problem_id      INTEGER   NOT NULL  REFERENCES problem(id),
  challenge_id    INTEGER             REFERENCES challenge(id),
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
  total_time    INTEGER,
  max_memory    INTEGER,
  score         INTEGER,  -- 保留設定扣分測資的空間
  judge_time    TIMESTAMP             NOT NULL
);

CREATE TABLE judgment_testdata_result (
  judgment_id INTEGER               NOT NULL REFERENCES judgment(id),
  testdata_id INTEGER               NOT NULL REFERENCES testdata(id),
  status      judgment_status_type  NOT NULL,
  time_lapse  INTEGER,
  peak_memory INTEGER,
  score       INTEGER,  -- 保留設定扣分測資的空間

  PRIMARY KEY (judgment_id, testdata_id)
);


-- Score

CREATE TABLE grade (
  id          SERIAL    PRIMARY KEY,
  receiver_id INTEGER   NOT NULL  REFERENCES account(id),
  grader_id   INTEGER   NOT NULL  REFERENCES account(id),
  class_id    INTEGER             REFERENCES class(id),
  item_name   VARCHAR   NOT NULL,
  score       INTEGER,
  comment     TEXT,
  update_time TIMESTAMP NOT NULL,

  UNIQUE (receiver_id, item_name)
);


-- Peer management

CREATE TABLE peer_review (
  id                  SERIAL    PRIMARY KEY,
  target_challenge_id INTEGER   NOT NULL  REFERENCES challenge(id),
  target_problem_id   INTEGER   NOT NULL  REFERENCES problem(id),
  description         TEXT,
  min_score           INTEGER   NOT NULL,
  max_score           INTEGER   NOT NULL,
  max_review_count    INTEGER   NOT NULL,  -- 一個人最多改幾份
  start_time          TIMESTAMP NOT NULL,
  end_time            TIMESTAMP NOT NULL,
  is_enabled          BOOLEAN   NOT NULL  DEFAULT false,
  is_hidden           BOOLEAN   NOT NULL  DEFAULT true
);

/* every receiver one record -> 要改的時候 edit record, add grader -> 改完 edit record, add comment
   when every receiver one record all reviewed -> every receiver add one new record */

CREATE TABLE peer_review_record (
  id                SERIAL    PRIMARY KEY,
  peer_review_id    INTEGER   NOT NULL  REFERENCES peer_review(id),
  grader_id         INTEGER   NOT NULL  REFERENCES account(id),
  receiver_id       INTEGER   NOT NULL  REFERENCES account(id),
  submission_id     INTEGER             REFERENCES submission(id),
  score             INTEGER,
  comment           TEXT,
  submit_time       TIMESTAMP NOT NULL,
  disagreement      TEXT,
  disagreement_time TIMESTAMP,

  UNIQUE (peer_review_id, grader_id, submission_id)
);


-- System

CREATE TABLE announcement (
  id          SERIAL    PRIMARY KEY,
  title       VARCHAR   NOT NULL,
  content     TEXT      NOT NULL,
  author_id   INTEGER   NOT NULL  REFERENCES account(id),
  post_time   TIMESTAMP NOT NULL,  -- 排程貼文
  expire_time TIMESTAMP NOT NULL   -- 自動下架
);

CREATE TABLE access_log (
  id              BIGSERIAL PRIMARY KEY,
  access_time     TIMESTAMP NOT NULL,
  request_method  VARCHAR   NOT NULL, -- Longest is `CONNECT` -> 7
  resource_path   VARCHAR   NOT NULL,
  ip              VARCHAR   NOT NULL, -- Linux `INET6_ADDRSTRLEN = 48` -> 47 + terminating NULL
  account_id      INTEGER   REFERENCES account(id)
);
