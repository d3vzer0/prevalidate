# Prevalidate

## Installation
```
# install poetry if not done before (ie. pip install poetry)
git clone https://github.com/d3vzer0/prevalidate.git
cd prevalidate
poetry install
```

## Commands
### Example
prevalidate sentinel unittest ../path_to_usecases ../path_to_schema

### Help
```
Usage: python -m prevalidate.main sentinel [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  sync      Sync Log Analytics workspace tables/fields
  unittest
```