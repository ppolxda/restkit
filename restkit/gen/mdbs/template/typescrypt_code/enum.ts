{% for name, row in enums.items() %}
{% if row['type'] != 'enum' %}{% continue %}{% end %}
export enum {{name}} { {% for key, val in row['fields'].items() %}
    {{key.upper()}} = {{val}},  // {{get_comments(row, key)}}{% end %}
}

export const {{name}}Translate = { {% for key, val in row['fields'].items() %}
    {{val}}: '{{get_comments(row, key)}}',{% end %}
}
{% end %}
