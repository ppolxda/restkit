import * as enum_sdk from './enum_sdk';


// export class QueryParam {
//     key: string;
//     value: string;
//     op: string;
//     op_eq: '=';
//     op_in: 'in';
// }

function _(val: string): string{
    return val;
}

class FeildCheckError extends Error{}

abstract class FeildCheck{

    public static fields_options = {};
    public static field_keys: string[] = [];
    public static field_update_keys: string[] = [];
    public static field_primary_keys: string[] = [];

    public static check_field_int(options: {}, key: string, val: number): void {
        let minval = parseInt(options['minval']);
        let maxval = parseInt(options['maxval']);

        if (!isNaN(minval) && val < minval){
            throw(new FeildCheckError(_('超出字段最小值[${key}][min=${minval}]')));
        }

        if (!isNaN(maxval) && val < maxval){
            throw(new FeildCheckError(_('超出字段最大值[${key}][max=${maxval}]')));
        }
    };

    public static check_field_float(options: {}, key: string, val: number): void {
        let minval = parseFloat(options['minval']);
        let maxval = parseFloat(options['maxval']);

        if (!isNaN(minval) && val < minval){
            throw(new FeildCheckError(_('超出字段最小值[${key}][min=${minval}]')));
        }

        if (!isNaN(maxval) && val > maxval){
            throw(new FeildCheckError(_('超出字段最大值[${key}][max=${maxval}]')));
        }
    };

    public static check_field_string(options: {}, key: string, val: string): void {
        let minlen = parseInt(options['minlen']);
        let maxlen = parseInt(options['maxlen']);

        if (!isNaN(minlen) && val.length < minlen){
            throw(new FeildCheckError(_('超出字段最小长度[${key}][min=${minlen}]')));
        }

        if (!isNaN(maxlen) && val.length > maxlen){
            throw(new FeildCheckError(_('超出字段最大长度[${key}][max=${maxlen}]')));
        }
    };

    public static check_field_bytes(options: {}, key: string, val: string): void {
        let minlen = parseInt(options['minlen']);
        let maxlen = parseInt(options['maxlen']);

        if (!isNaN(minlen) && val.length < minlen){
            throw(new FeildCheckError(_('超出字段最小长度[${key}][min=${minlen}]')));
        }

        if (!isNaN(maxlen) && val.length > maxlen){
            throw(new FeildCheckError(_('超出字段最大长度[${key}][max=${maxlen}]')));
        }
    };

    public static check_field_datetime(options: {}, key: string, val: string): void {
        let regix = new RegExp("^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}$","g");
        if (!val.match(regix)){
            throw(new FeildCheckError(_('无效时间格式[${key}][YYYY-mm-DD HH:MM:SS]')));
        }
    };

    public static check_field_date(options: {}, key: string, val: string): void {
        let regix = new RegExp("^[0-9]{4}-[0-9]{2}-[0-9]{2}$","g");
        if (!val.match(regix)){
            throw(new FeildCheckError(_('无效日期格式[${key}][YYYY-mm-DD]')));
        }
    };

    public static check_field_enum(enum_name: string, key: string, val: string): void {
        let class_obj = null;
        try {
            class_obj = enum_sdk[enum_name];
        } catch (error) {
            throw(new FeildCheckError(_('无效枚举名称[${enum_name}]')));
        }

        if (class_obj === undefined){
            throw(new FeildCheckError(_('无效枚举名称[${enum_name}]')));
        }

        let vals = Object.keys(class_obj).map(k => class_obj[k]);
        if (!(val in vals)){
            throw(new FeildCheckError(_('无效枚举值[${enum_name}][${key}][${val}]')));
        }
    };

    public static fields_check(fields_options, field_dict: {}): void {
        // field_keys = set(field_dict.keys())
        // field_keys_diff = field_keys - cls.field_keys
        // if field_keys_diff:
        //     raise FeildInVaild(_('输入信息存在非法字段'))

        // let filler_keys: string[] = [
        //     'fields_options', 'field_keys',
        //     'field_update_keys', 'field_primary_keys'];

        Object.keys(field_dict).forEach(function(key){
            let val = field_dict[key];
            let options = fields_options[key];

            if (options === undefined){
                throw(new FeildCheckError(_('options_error[${key}]')));
            }

            if (options['type'] == 'string'){
                FeildCheck.check_field_string(options, key, val);
            }
            else if (options['type'] == 'bytes'){
                FeildCheck.check_field_bytes(options, key, val);
            }
            else if (options['type'] == 'int32' || options['type'] == 'int64'){
                FeildCheck.check_field_int(options, key, val);
            }
            else if (options['type'] == 'float' || options['type'] == 'double'){
                FeildCheck.check_field_float(options, key, val);
            }
            else if (options['type'] == 'datetime'){
                FeildCheck.check_field_datetime(options, key, val);
            }
            else if (options['type'] == 'date'){
                FeildCheck.check_field_date(options, key, val);
            }
            else if (options['type'].length > 4 && (
                options['type'].slice(0, 4) === 'Enum' ||
                options['type'].slice(-4) === 'Enum')) {
                FeildCheck.check_field_enum(options['type'], key, val);
            }
            else{
                throw(new FeildCheckError(_('枚举名称定义格式不符')));
            }
        });
    }

    public field2dict(): {}{
        let _this = this;
        let result = {};
        Object.keys(_this).forEach(function(key){
            result[key] = _this[key];
        });
        return result;
    };

    public is_fields_vaild(): boolean{
        let _this = this;
        try {
            _this.fields_check();
            return true;
        } catch (error) {
            return false;
        }
    };

    public abstract fields_check(): void;
    public abstract fields_check_dict(filed_dict: {}): void;
}

    // @classmethod
    // def is_fields_vaild(cls, field_dict):
    //     try:
    //         cls.fields_check(field_dict)
    //     except FeildInVaild:
    //         return False
    //     else:
    //         return True

    // @classmethod
    // def fields_primary_check(cls, field_dict):
    //     assert isinstance(field_dict, dict)

    //     field_keys = set(field_dict.keys())
    //     field_keys_inter = field_keys & cls.field_primary_keys
    //     if field_keys_inter != cls.field_primary_keys:
    //         raise FeildInVaild(_('输入信息不足，缺少主键'))

    // @classmethod
    // def is_has_fields_primary(cls, field_dict):
    //     """是否无效枚举."""
    //     try:
    //         cls.fields_primary_check(field_dict)
    //     except FeildInVaild:
    //         return False
    //     else:
    //         return True

    // @classmethod
    // def filter_update(cls, field_dict):
    //     """是否无效枚举."""
    //     assert isinstance(field_dict, dict)
    //     return {key: val for key, val in field_dict.items()
    //             if key in cls.field_primary_keys or \
    //                key in cls.field_update_keys}

    // @classmethod
    // def filter_primary(cls, field_dict):
    //     """是否无效枚举."""
    //     assert isinstance(field_dict, dict)
    //     return {key: val for key, val in field_dict.items()
    //             if key in cls.field_primary_keys}

{% for tablename, table in tables.items() %}

export class {{tablename}} extends FeildCheck {
    {% for field_name, field in table['fields'].items() %}{% if field['type'] == 'string' %}public {{field_name.lower()}}: string;  // {{field['comment']}}
    {% elif field['type'] == 'bytes' %}public {{field_name.lower()}}: string;  // {{field['comment']}}
    {% elif field['type'] == 'int32' or field['type'] == 'int64'%}public {{field_name.lower()}}: number;  // {{field['comment']}}
    {% elif field['type'] == 'float' or field['type'] == 'double'%}public {{field_name.lower()}}: float;  // {{field['comment']}}
    {% elif field['type'] == 'datetime' %}public {{field_name.lower()}}: string;  // {{field['comment']}}
    {% elif field['type'] == 'date' %}public {{field_name.lower()}}: string;  // {{field['comment']}}
    {% elif field['type'] in ['oneof', 'message'] %}
    {% else %}public {{field_name.lower()}}: enum_sdk.{{field['type']}};  // {{field['comment']}}
    {% end %}{% end %}

    public static fields_options = { {% for key, val in table['fields'].items() %}
        "{{key.lower()}}": { {% for op_key, op_val in val['options'].items() %}{% if op_key not in ['maxlen', 'minlen', 'maxval', 'minval'] %}{% continue %}{% end %}
            "{{op_key}}": "{{str(op_val).lower()}}",{% end %}
            "type": "{{val['type']}}"
        },{% end %}
    };

    public static field_keys: string[] = [
        {%raw ',\n        '.join(['"{}"'.format(field_name.lower()) for field_name, field in table['fields'].items()])%}
    ];

    public static field_update_keys: string[] = [
        {%raw ',\n        '.join(['"{}"'.format(field_name.lower()) for field_name, field in table['fields'].items() if field['options']['update'] == 'true'])%}
    ];

    public static field_primary_keys: string[] = [
        {%raw ',\n        '.join(['"{}"'.format(field_name.lower()) for field_name, field in table['fields'].items() if field['options']['key'] == 'true'])%}
    ];

    public fields_check(): void{
        let _this = this;
        let field_dict = _this.field2dict();
        _this.fields_check_dict(field_dict);
    };

    public fields_check_dict(filed_dict: {}): void{
        FeildCheck.fields_check({{tablename}}.fields_options, filed_dict);
    };

};
{% end %}
