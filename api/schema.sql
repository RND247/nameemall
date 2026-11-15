-- NameEmAll Daily results (anonymous). One ranked result per player per daily per mode.
-- player_id is a random ID generated in the browser; no names, emails or raw IPs are stored.
CREATE TABLE IF NOT EXISTS daily_results (
  day        INTEGER NOT NULL,          -- Daily number (#1 = 2026-04-30)
  mode       TEXT    NOT NULL,          -- 'mini' | 'midi'
  player_id  TEXT    NOT NULL,          -- random UUID kept in the player's browser
  score      INTEGER NOT NULL,          -- Pokémon named
  total      INTEGER NOT NULL,          -- 5 or 30
  time_ms    INTEGER NOT NULL,
  gave_up    INTEGER NOT NULL DEFAULT 0,
  found      TEXT    NOT NULL,          -- '0'/'1' per Pokémon in the daily's fixed order
  lang       TEXT,
  ip_hash    TEXT,                      -- salted daily hash, only for rate limiting
  created_at INTEGER NOT NULL,
  PRIMARY KEY (day, mode, player_id)
);

CREATE INDEX IF NOT EXISTS idx_daily_rank ON daily_results (day, mode, score, time_ms);
CREATE INDEX IF NOT EXISTS idx_daily_ip ON daily_results (day, ip_hash);

-- Device transfer (no accounts): the browser encrypts its progress with a random code it shows the player.
-- The server only sees a SHA-256 fingerprint of that code and the encrypted blob, which expires after 24 hours.
CREATE TABLE IF NOT EXISTS transfers (
  id         TEXT    PRIMARY KEY,         -- hex SHA-256 of the code (the code itself never reaches the server)
  data       TEXT    NOT NULL,            -- base64 AES-GCM ciphertext
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS transfer_hits (
  ip_hash TEXT    NOT NULL,               -- salted daily IP hash, only for rate limiting
  day     INTEGER NOT NULL,
  kind    TEXT    NOT NULL,               -- 'put' | 'get'
  n       INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (ip_hash, day, kind)
);
