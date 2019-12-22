# {{method}} {% raw path %}

## apikey flag

{% raw api_key %}

## Api description

{% raw desc %}

## Http Query Parames Request

name|type|required|default|memo|other
:---|:--:|:--:|:---|:---|:---
{% raw query_parames %}

## Http Body Parames Request

name|type|required|default|memo|other
:---|:--:|:--:|:---|:---|:---
{% raw req_parames %}

## Http Body Parames Response

name|type|required|default|memo|other
:---|:--:|:--:|:---|:---|:---
{% raw rsp_parames %}

## Http Body Parames Request Json

```json
{% raw req_json_parames %}
```

## Http Body Parames Response Json

```json
{% raw rsp_json_parames %}
```

{% if method == 'GET' %}

## Query Json Description

```json
{% raw query_json_parames %}
```

## Query Desc

Http Get Query Parames Request
where: Query Condition,use mongo stype parames
page: Query Page, Step or limit
sort: Query Srot

### Where Query Condition, use mongo stype parames

https://docs.mongodb.com/manual/reference/operator/query/

#### Where example

SQL Stype

```sql
key1=value1 and
key2=value2 and
key3 in (a,b,c) and
key4 > 0 and
key5 >= 0 and
key6 < 0 and
key7 <= 0 and
key8 <> 0 and
key9 like 'abc%' and
key10 between '1900-01-01' and '1900-01-02' and
key11 not in (a,b,c) and
```

SQL Stype to Mongo Stype JSON

```json
{
    "key1": "value1",
    "key2": "value2",
    "key3": {'$in': [a,b,c]},
    "key4": {'$gt': 0},
    "key5": {'$gte': 0},
    "key6": {'$lt': 0},
    "key7": {'$lte': 0},
    "key8": {'$ne': 0},
    "key9": {'$like': 'abc%'},
    "key10": {'$between': ['1900-01-01', '1900-01-02']},
    "key11": {'$nin': [a,b,c]},
}
```

### Page json

max limit 500

limit = [0, 100] --- [step, limit]

### Sort json

sorts = {'key1': 'desc', 'key2': 'asc'}

{% end %}
