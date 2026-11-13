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
