
{% for tablename, table in tables.items() %}
-- ----------------------------
-- Table structure for `{{dbname}}`.{{ tablename }}
-- ----------------------------
-- DROP TABLE IF EXISTS `{{dbname}}`.`{{tablename}}`;
CREATE TABLE `{{dbname}}`.`{{tablename}}` (
`createtime`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
`updatetime`  timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
{% for field_name, field in table['fields'].items() %}{% if field['type'] == 'string' %}`{{field_name}}`  varchar({{field['options']['maxlen']}}) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL {% if field['options']['default']%} DEFAULT {%raw field['options']['default']%} {% end %},
{% elif field['type'] == 'bytes' %}`{{field_name}}`  varbinary({{field['options']['maxlen']}}) NOT NULL {% if field['options']['default']%} DEFAULT {%raw field['options']['default']%} {% end %},
{% elif field['type'] == 'int32' or field['type'] == 'int64'%}`{{field_name}}`  int(11) NOT NULL {% if field['options']['inc'] %}AUTO_INCREMENT{% end %} {% if field['options']['default']%} DEFAULT {%raw field['options']['default']%} {% end %},
{% elif field['type'] == 'float' or field['type'] == 'double'%}`{{field_name}}`  {% if field['options']['maxlen'] %} decimal({{field['options']['maxlen']}}){% else %} decimal(16,6) {% end %} NOT NULL {% if field['options']['default']%} DEFAULT {%raw field['options']['default']%} {% end %},
{% elif field['type'] == 'datetime' %}`{{field_name}}`  datetime NOT NULL {% if field['options']['default']%} DEFAULT {%raw field['options']['default']%} {% end %},
{% elif field['type'] == 'date' %}`{{field_name}}`  date NOT NULL {% if field['options']['default']%} DEFAULT {%raw field['options']['default']%} {% end %},
{% elif field['type'] in ['oneof', 'message'] %}
{% else %}`{{field_name}}` char(2) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL {% if field['options']['default']%} DEFAULT {%raw enums[field['type']]['fields'][field['options']['default']]%} {% end %},
{% end %}{% end %}PRIMARY KEY ({% raw json_encode(table['keys'])[1:-1].replace('"', '`') %})
)
ENGINE=InnoDB
DEFAULT CHARACTER SET=utf8 COLLATE=utf8_general_ci
;
{% end %}
