{% for tablename, _table in tables.items() %}
{% if len(_table['nested']) <= 0 %}{% continue %}{% end %}
{% set nested_keys = list(_table['nested'].keys()) %}

{% for field_name in nested_keys %}
-- ----------------------------
-- Table structure for {{ dbname }}.{{ tablename }}
-- ----------------------------
ALTER TABLE `{{ dbname }}`.`{{ tablename }}`{%set field = _table['nested'][field_name] %}
{% if field_name.lower().endswith('unique') %}ADD UNIQUE INDEX `{{field_name}}` ({% raw ', '.join(field['fields'].keys()) %}) USING BTREE;
{% elif field_name.lower().endswith('index') %}ADD INDEX `{{field_name}}` ({% raw ', '.join(field['fields'].keys()) %}) USING BTREE;
{% elif field_name.lower().endswith('foreign') %}{% end %}{% end %}
{% end %}
