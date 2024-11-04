
CREATE TABLE IF NOT EXISTS category (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT
);

CREATE TABLE IF NOT EXISTS question (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category INTEGER,
  question TEXT,
  FOREIGN KEY(category) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS answer (
  question INTEGER,
  choice TEXT, -- a, b, c, etc
  answer TEXT,
  correct BOOLEAN,
  FOREIGN KEY(question) REFERENCES question(id)
)

CREATE TABLE IF NOT EXISTS user (
  userid TEXT PRIMARY KEY,
  pending_question INTEGER NULL
  FOREIGN KEY(pending_question) REFERENCES question(id)
);

CREATE TABLE IF NOT EXISTS response (
  userid TEXT,
  question INTEGER,
  answer INTEGER,
  timestamp INTEGER,
  correct BOOLEAN,
  FOREIGN KEY (userid) REFERENCES user(userid)
);