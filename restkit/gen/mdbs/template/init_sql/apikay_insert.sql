-- ------------------------------------
-- {{service_name}}
-- ------------------------------------
{% for api_name, api_info in api_config.items() %}{% if api_info.get('is_debug', False) %}{% continue %}{% end %}
INSERT INTO "admins"."sys_apikeys" ( "apikey", "servicename", "method", "nginxuri", "apiuri" ) VALUES ('{{api_info['api_key']}}', '{{service_name}}', '{{api_info['method']}}', '{{api_info['nginx_uri']}}', '{{api_info['api_uri']}}');
{% end %}