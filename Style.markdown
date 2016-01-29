# Stanford OpenEdX Style Guide

## Python

### Trailing Commas

#### Implementation

Wherever syntactically allowed, always add a trailing comma to iterables.

##### Good

```python
item = ItemFactory.create(
    parent_location=parent.location,
    category=category,
    metadata=metadata,
)
```

##### Bad
```python
item = ItemFactory.create(
    parent_location=parent.location,
    category=category,
    metadata=metadata
)
```

#### Theory

By appending a trailing comma to iterables, we're able to add additional
lines/items to the collection without altering previous items.
This provides a cleaner diff when viewing the version control history.
It also reduces the likelihood of conflicts while merging.


### Single vs Double Quotes

#### Implementation

Use single quotes, by default. Exceptions include:
- interpolated strings
- strings that contain literal double-quotes

##### Good

```python
foo['literal'] = 'single'
foo['interpolated'] = "{number} quotes".format(
    number='double',
)
foo['mix'] = "It's painful to escape the author's quotes here."
```

##### Bad
```python
foo["literal"] = "single"
foo["interpolated"] = '{number} quotes'.format(
    number="double",
)
foo["mix"] = 'It\'s painful to escape the author\'s quotes here.'
```

#### Theory

blah blah blah



### Use string formatting instead of concatenation

#### Implementation

##### Good
```python
msg = "setting_type {setting_type} does not match".format(
    setting_type=str(setting_type),
)
```

##### Bad
```python
msg = 'setting_type' + str(setting_type) + 'does not match'
```

Superfluous comment
self.about_sidebar_html = ""  # html to render as the about_sidebar_html

dict formatting
`{` alignment

long import lines
- no continuation!
