set -e
psql -h localhost -p 5432 -U root -d shop_data << EOSQL
CREATE TABLE user_transaction(
  user_id       VARCHAR(100),
  product_id    INT(11),
  bought        BOOLEAN DEFAULT FALSE,
  created_at    DATETIME,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_checkin(
  user_id       VARCHAR(100),
  status        ENUM("checkin", "checkout") DEFAULT "checkin",
  created_at    DATETIME,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products(
  product_id    INT(11) NOT NULL,
  product_name  VARCHAR(100),
  price         INT(11) DEFAULT 0,
  PRIMARY KEY (product_id)
);

EOSQL
