{% for tablename, _table in tables.items() %}
{% if len(_table['nested']) <= 0 %}{% continue %}{% end %}
{% set nested_keys = list(_table['nested'].keys()) %}
-- ----------------------------
-- Table structure for {{ dbname }}.{{ tablename }}
-- ----------------------------
ALTER TABLE `{{ dbname }}`.`{{ tablename }}`
{% for field_name in nested_keys %}{%set field = _table['nested'][field_name] %}
{% if field_name.lower().endswith('unique') %}ADD UNIQUE INDEX `{{field_name}}` ({% raw ', '.join(field['fields'].keys()) %}) USING BTREE{% if nested_keys.index(field_name) != (len(nested_keys) - 1) %},{% else %};{% end %}
{% elif field_name.lower().endswith('index') %}ADD INDEX `{{field_name}}` ({% raw ', '.join(field['fields'].keys()) %}) USING BTREE{% if  nested_keys.index(field_name) != (len(nested_keys) - 1) %},{% else %};{% end %}
{% elif field_name.lower().endswith('foreign') %}{% end %}{% end %}
{% end %}
