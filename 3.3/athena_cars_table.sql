CREATE EXTERNAL TABLE IF NOT EXISTS cars (
  ad_id BIGINT,
  subject STRING,
  price BIGINT,
  list_time STRING,
  share_url STRING,
  seller_name STRING,
  seller_type STRING,
  brand STRING,
  model STRING,
  year INT,
  mileage STRING,
  fuel STRING,
  gearbox STRING,
  location STRING,
  zipcode STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://blocked-data-15/flat/'
TBLPROPERTIES ('skip.header.line.count'='1');
