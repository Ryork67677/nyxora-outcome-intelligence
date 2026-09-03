# Widget API v2

## Limits

The maximum output value is 200 units. In Widget API v1, the documented maximum was 100 units.

## Parameters

`max_output_units` controls the maximum number of output units returned by the API.

```python
client.widgets.create(max_output_units=200)
```
