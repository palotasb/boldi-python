# Boldi Python monorepo

## Contributing

### Prerequisites

```shell
brew install python@3.12
```

### Clear existing dev env

```shell
[ -n "${VIRTUAL_ENV:-}" ] && deactivate
rm -rf .venv pdm.lock
```

### Create dev env

```shell
python3.12 -m venv .venv
. .venv/bin/activate
pip install pdm
pdm install
```
