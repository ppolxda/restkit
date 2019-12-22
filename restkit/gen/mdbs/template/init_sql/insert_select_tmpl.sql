
{% for tablename, table in tables.items() %}{% if tablename in ['coin_umfee_log'] or 'options' not in table or 'snapshot' not in table['options'] or not table['options']['snapshot'] %}{% continue %}{% end %}
-- ----------------------------
-- Table structure for `{{dbname}}`.{{ tablename }}
-- ----------------------------
INSERT INTO  {{dbname}}.snapshot_{{tablename}}
(
    "createtime",
    "updatetime",
    "snapshottime",
    {%raw ',\n    '.join(['"' + field_name.lower() + '"' for field_name in table['fields']])%}
) 
SELECT
    {{dbname}}.{{tablename}}.createtime,
    {{dbname}}.{{tablename}}.updatetime,
    stime,
    {{',\n    '.join([dbname + '.' + tablename + '.' + field_name.lower() for field_name in table['fields']])}}
FROM
    {{dbname}}.{{tablename}};
{% end %}