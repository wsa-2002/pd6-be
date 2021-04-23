CREATE DATABASE pdogs;

USE pdogs;

-- RBAC

CREATE TABLE role (
  id    INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name  VARCHAR(32) NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (name)
);

CREATE TABLE permission (
  id    INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name  VARCHAR(32) NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (name)
);

CREATE TABLE role_permission (
  role_id       INT     UNSIGNED  NOT NULL,
  permission_id INT     UNSIGNED  NOT NULL,
  is_active     BOOLEAN NOT NULL  DEFAULT false,

  PRIMARY KEY (role_id, permission_id),
  FOREIGN KEY (role_id) REFERENCES role(id),
  FOREIGN KEY (permission_id) REFERENCES permission(id)
);


-- Account

CREATE TABLE institute (
  id            INT           UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name          VARCHAR(32)   NOT NULL,
  email_domain  VARCHAR(255)  NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (name),
  UNIQUE (email_domain)
);

CREATE TABLE student_card (
  id            INT           UNSIGNED  NOT NULL  AUTO_INCREMENT,
  institute_id  INT           NOT NULL,
  department    VARCHAR(32)   NOT NULL,
  student_id    VARCHAR(32)   NOT NULL,
  email         VARCHAR(255)  NOT NULL,
  is_enabled    BOOLEAN       NOT NULL  DEFAULT false,

  PRIMARY KEY (id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  FOREIGN KEY (institute_id) REFERENCES institute(id),

  UNIQUE (institute_id, student_id),
  UNIQUE (student_id)  -- for functional safety
);

CREATE TABLE account (
  id                INT             UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name              VARCHAR(32)     NOT NULL,
  pass_salt         VARBINARY(128)  NOT NULL,
  pass_hash         VARBINARY(128)  NOT NULL,
  nickname          VARCHAR(255)    NOT NULL,
  real_name         VARCHAR(32)     NOT NULL,
  role_id           INT             UNSIGNED  NOT NULL,  -- global role
  alternative_email VARCHAR(255)    ,
  is_enabled        BOOLEAN         NOT NULL  DEFAULT false,
--  is_hidden     BOOLEAN         NOT NULL  DEFAULT false,

  PRIMARY KEY (id),
  FOREIGN KEY (role_id) REFERENCES role(id),
  UNIQUE (name),
  UNIQUE (email)
);


-- Course management

CREATE TABLE course_type (
  id    INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name  VARCHAR(32) NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (name)
);

CREATE TABLE course (
  id          INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name        VARCHAR(32) NOT NULL,
  type_id     INT         UNSIGNED  NOT NULL,
  is_enabled  BOOLEAN     NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN     NOT NULL  DEFAULT true,

  PRIMARY KEY (id),
  FOREIGN KEY (type_id) REFERENCES course_type(id),
  UNIQUE (name)
);

CREATE TABLE course_member (
  course_id   INT     UNSIGNED  NOT NULL,
  account_id  INT     UNSIGNED  NOT NULL,
  role_id     INT     UNSIGNED  NOT NULL,
  is_enabled  BOOLEAN NOT NULL  DEFAULT false,

  PRIMARY KEY (course_id, account_id),
  FOREIGN KEY (course_id) REFERENCES course(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  FOREIGN KEY (role_id) REFERENCES role(id)
);

CREATE TABLE class (
  id          INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  course_id   INT         UNSIGNED  NOT NULL,
  name        VARCHAR(32) NOT NULL,
  is_enabled  BOOLEAN     NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN     NOT NULL  DEFAULT true,
  
  PRIMARY KEY (id),
  FOREIGN KEY (course_id) REFERENCES course(id),
  UNIQUE (course_id, name)
);

CREATE TABLE class_member (
  class_id    INT     UNSIGNED  NOT NULL,
  account_id  INT     UNSIGNED  NOT NULL,
  role_id     INT     UNSIGNED  NOT NULL,
  is_enabled  BOOLEAN NOT NULL  DEFAULT false,

  PRIMARY KEY (class_id, account_id),
  FOREIGN KEY (class_id) REFERENCES class(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  FOREIGN KEY (role_id) REFERENCES role(id)
);

CREATE TABLE team (
  id          INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  class_id    INT         UNSIGNED  NOT NULL,
  name        VARCHAR(32) NOT NULL,
  is_enabled  BOOLEAN     NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN     NOT NULL  DEFAULT true,

  PRIMARY KEY (id),
  FOREIGN KEY (class_id) REFERENCES class(id),
  UNIQUE (class_id, name)
);

CREATE TABLE team_member (
  team_id     INT     UNSIGNED  NOT NULL,
  account_id  INT     UNSIGNED  NOT NULL,
  role_id     INT     UNSIGNED  NOT NULL,
  is_enabled  BOOLEAN NOT NULL  DEFAULT false,

  PRIMARY KEY (team_id, account_id),
  FOREIGN KEY (team_id) REFERENCES team(id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  FOREIGN KEY (role_id) REFERENCES role(id)
);


-- Challenge-problem management

CREATE TABLE challenge_type (
  id    INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name  VARCHAR(32) NOT NULL,
  
  PRIMARY KEY (id),
  UNIQUE (name)
);

CREATE TABLE challenge (
  id          INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  class_id    INT         UNSIGNED  NOT NULL,
  type_id     INT         UNSIGNED  NOT NULL,
  name        VARCHAR(32) NOT NULL,
  setter_id   INT         UNSIGNED  NOT NULL,
  description TEXT,
  start_time  DATETIME    NOT NULL,
  end_time    DATETIME    NOT NULL,
  is_enabled  BOOLEAN     NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN     NOT NULL  DEFAULT true,

  PRIMARY KEY (id),
  FOREIGN KEY (class_id) REFERENCES class(id),
  FOREIGN KEY (type_id) REFERENCES challenge_type(id),
  FOREIGN KEY (setter_id) REFERENCES account(id),
  UNIQUE (class_id, name)
);

-- 'judge',
-- 'options',
-- 'file',
-- 'peer',
-- 'project'
-- 'special'

CREATE TABLE problem_type (
  id    INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name  VARCHAR(32) NOT NULL,
  
  PRIMARY KEY (id),
  UNIQUE (name)
);

CREATE TABLE problem (
  id          INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  type_id     INT         UNSIGNED  NOT NULL,
  name        VARCHAR(32) NOT NULL,
  setter_id   INT         UNSIGNED  NOT NULL,
  full_score  INT         UNSIGNED  NOT NULL,
  description TEXT,
  source      TEXT,
  hint        TEXT,
  is_enabled  BOOLEAN     NOT NULL  DEFAULT false,
  is_hidden   BOOLEAN     NOT NULL  DEFAULT true,

  PRIMARY KEY (id),
  FOREIGN KEY (type_id) REFERENCES problem_type(id),
  FOREIGN KEY (setter_id) REFERENCES account(id),
  UNIQUE (name)
);

CREATE TABLE testdata (
  id            INT     UNSIGNED  NOT NULL  AUTO_INCREMENT,
  problem_id    INT     UNSIGNED  NOT NULL,
  is_sample     BOOLEAN NOT NULL,
  score         INT     NOT NULL, -- 保留設定扣分測資的空間
  input_file    TEXT,
  ouptut_file   TEXT,
  time_limit    INT     UNSIGNED, -- ms
  memory_limit  INT     UNSIGNED, -- kb
  is_enabled    BOOLEAN NOT NULL  DEFAULT false,
  is_hidden     BOOLEAN NOT NULL  DEFAULT true,

  PRIMARY KEY (id),
  FOREIGN KEY (problem_id) REFERENCES problem(id)
);

CREATE TABLE challenge_problem (
  challenge_id  INT UNSIGNED  NOT NULL,
  problem_id    INT UNSIGNED  NOT NULL,

  PRIMARY KEY (challenge_id, problem_id),
  FOREIGN KEY (challenge_id) REFERENCES challenge(id),
  FOREIGN KEY (problem_id) REFERENCES problem(id)
);


-- submission management

CREATE TABLE submission_language (
  id      INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  name    VARCHAR(32) NOT NULL,
  version VARCHAR(32) NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (name, version)
);

CREATE TABLE submission (
  id              INT       UNSIGNED  NOT NULL  AUTO_INCREMENT,
  account_id      INT       UNSIGNED  NOT NULL,
  problem_id      INT       UNSIGNED  NOT NULL,
  challenge_id    INT       UNSIGNED,
  language_id     INT       UNSIGNED  NOT NULL,
  content_file    TEXT      NOT NULL,
  content_length  SMALLINT  UNSIGNED  NOT NULL, -- 因為 TEXT 也只能存到 65535
  submit_time     DATETIME  NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (account_id) REFERENCES account(id),
  FOREIGN KEY (problem_id) REFERENCES problem(id),
  FOREIGN KEY (challenge_id) REFERENCES challenge(id),
  FOREIGN KEY (language_id) REFERENCES submission_language(id)
);

-- AC
-- WA
-- TLE
CREATE TABLE judgment_result (
  id        INT         UNSIGNED  NOT NULL  AUTO_INCREMENT,
  priority  TINYINT     UNSIGNED  NOT NULL,
  name      VARCHAR(32) NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (priority),
  UNIQUE (name)
);

-- rejudge => one submission many judgement

CREATE TABLE judgment (
  id            INT UNSIGNED  NOT NULL  AUTO_INCREMENT,
  submission_id INT UNSIGNED  NOT NULL,
  result_id     INT UNSIGNED  NOT NULL,
  total_time    INT UNSIGNED,
  max_memory    INT UNSIGNED,
  score         INT, -- 保留設定扣分測資的空間
  judge_time    DATETIME      NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (submission_id) REFERENCES submission(id),
  FOREIGN KEY (result_id) REFERENCES judgment_result(id)
);

CREATE TABLE judgment_testdata_result (
  judgment_id INT UNSIGNED  NOT NULL,
  testdata_id INT UNSIGNED  NOT NULL,
  result_id   INT UNSIGNED  NOT NULL,
  time_lapse  INT UNSIGNED,
  peak_memory INT UNSIGNED,
  score       INT, -- 保留設定扣分測資的空間

  PRIMARY KEY (judgment_id, testdata_id),
  FOREIGN KEY (judgment_id) REFERENCES judgment(id),
  FOREIGN KEY (testdata_id) REFERENCES testdata(id),
  FOREIGN KEY (result_id) REFERENCES judgment_result(id)
);


-- Score

CREATE TABLE grade (
  id          INT           UNSIGNED  NOT NULL  AUTO_INCREMENT,
  receiver_id INT           UNSIGNED  NOT NULL,
  grader_id   INT           UNSIGNED  NOT NULL,
  class_id    INT           UNSIGNED,
  item_name   VARCHAR(255)  NOT NULL,
  score       INT,
  comment     TEXT,
  update_time DATETIME      NOT NULL,

  PRIMARY KEY (id),
  FOREIGN KEY (receiver_id) REFERENCES account(id),
  FOREIGN KEY (grader_id) REFERENCES account(id),
  FOREIGN KEY (class_id) REFERENCES class(id),
  UNIQUE (receiver_id, item_name)
);


-- Peer management

CREATE TABLE peer_review (
  id                  INT       UNSIGNED  NOT NULL  AUTO_INCREMENT,
  target_challenge_id INT       UNSIGNED  NOT NULL,
  target_problem_id   INT       UNSIGNED  NOT NULL,
  description         TEXT,
  min_score           TINYINT   UNSIGNED  NOT NULL,
  max_score           TINYINT   UNSIGNED  NOT NULL,
  max_review_count    TINYINT   UNSIGNED  NOT NULL,  -- 一個人最多改幾份
  start_time          DATETIME  NOT NULL,
  end_time            DATETIME  NOT NULL,
  is_enabled          BOOLEAN   NOT NULL  DEFAULT false,
  is_hidden           BOOLEAN   NOT NULL  DEFAULT true,

  PRIMARY KEY (id),
  FOREIGN KEY (target_challenge_id) REFERENCES challenge(id),
  FOREIGN KEY (target_problem_id) REFERENCES problem(id)
);

/* every receiver one record -> 要改的時候 edit record, add grader -> 改完 edit record, add comment
   when every receiver one record all reviewed -> every receiver add one new record */

CREATE TABLE peer_review_record (
  id                  INT       UNSIGNED  NOT NULL  AUTO_INCREMENT,
  peer_review_id      INT       UNSIGNED  NOT NULL,
  grader_id           INT       UNSIGNED  NOT NULL,
  receiver_id         INT       UNSIGNED  NOT NULL,
  submission_id       INT       UNSIGNED,
  score               TINYINT   UNSIGNED,
  comment             TEXT,
  submit_time         DATETIME  NOT NULL,
  disagreement        TEXT,
  disagreement_time   DATETIME,

  PRIMARY KEY (id),
  FOREIGN KEY (peer_review_id) REFERENCES peer_review(id),
  FOREIGN KEY (grader_id) REFERENCES account(id),
  FOREIGN KEY (receiver_id) REFERENCES account(id),
  FOREIGN KEY (submission_id) REFERENCES submission(id),
  UNIQUE (peer_review_id, grader_id, submission_id)
);


-- System

CREATE TABLE announcement (
  id          INT           UNSIGNED  NOT NULL  AUTO_INCREMENT,
  title       VARCHAR(255)  NOT NULL,
  content     TEXT          NOT NULL,
  author_id   INT           NOT NULL,
  post_time   DATETIME      NOT NULL,  -- 排程貼文
  expire_time DATETIME      NOT NULL,  -- 自動下架

  PRIMARY KEY (id),
  FOREIGN KEY (author_id) REFERENCES account(id)
);

CREATE TABLE access_log (
  id              BIGINT        UNSIGNED  NOT NULL  AUTO_INCREMENT,
  access_time     DATETIME      NOT NULL,
  request_method  VARCHAR(7)    NOT NULL, -- Longest is `CONNECT` -> 7
  resource_path   VARCHAR(255)  NOT NULL,
  ip              VARCHAR(47)   NOT NULL, -- Linux `INET6_ADDRSTRLEN = 48` -> 47 + terminating NULL
  account_id      INT           UNSIGNED,

  PRIMARY KEY (id),
  FOREIGN KEY (account_id) REFERENCES account(id)
);
