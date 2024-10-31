CREATE TABLE IF NOT EXISTS node (
    id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS message (
    fromId TEXT,
    toId TEXT,
    timestamp INTEGER,
    payload TEXT,
    FOREIGN KEY(fromId) REFERENCES node(id),
    FOREIGN KEY(toId) REFERENCES node(id)
);

CREATE TABLE IF NOT EXISTS position (
    id INTEGER PRIMARY KEY,
    node TEXT,
    timestamp INTEGER,
    latitude REAL,
    longitude REAL,
    altitude INTEGER,
    FOREIGN KEY(node) REFERENCES node(id)
);

CREATE TABLE IF NOT EXISTS node_info (
    id INTEGER PRIMARY KEY,
    node TEXT,
    timestamp INTEGER,
    longName TEXT,
    shortName TEXT,
    macaddr TEXT,
    hwModel TEXT,
    FOREIGN KEY(node) REFERENCES node(id)
);

CREATE TABLE IF NOT EXISTS device_metric (
    id INTEGER PRIMARY KEY,
    node TEXT,
    timestamp TEXT,
    batteryLevel REAL,
    channelUtilization REAL,
    airUtilTx REAL,
    uptimeSeconds REAL,
    FOREIGN KEY(node) REFERENCES node(id)
);

CREATE TABLE IF NOT EXISTS environment_metric (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    node TEXT,
    -- time INTEGER NOT NULL,
    temperature REAL,
    relative_humidity REAL,
    barometric_pressure REAL,
    gas_resistance REAL,
    voltage REAL,
    current REAL,
    iaq INTEGER,
    distance REAL,
    lux REAL,
    white_lux REAL,
    ir_lux REAL,
    uv_lux REAL,
    wind_direction INTEGER,
    wind_speed REAL,
    weight REAL,
    wind_gust REAL,
    wind_lull REAL,
    FOREIGN KEY(node) REFERENCES node(id)
);



-- INSERT INTO node VALUES ('abc');
-- INSERT INTO node VALUES ('def');

-- INSERT INTO message (timestamp, fromId, toId, payload)
-- VALUES (datetime(), 'abc', 'def', 'hi dude');

-- INSERT INTO message (timestamp, fromId, toId, payload)
-- VALUES (datetime(), 'def', 'abc', 'sup man');

-- INSERT INTO message (timestamp, fromId, toId, payload)
-- VALUES (datetime(), 'abc', 'def', 'not much');

