# Anisodactyl

## Quickstart

```sh
git clone https://github.com/MidHunterX/Anisodactyl.git
cd Anisodactyl
pip install -e .[dev]
```

### Nice Test UI

Adds colorful CLI progress bars, check icons and coloured diff on `pytest -vv`.
Nice on eyes, fast and faithful to the original pytest interface. Very minimal.

```sh
pip install -e .[dev,nice]
```

### Fancy Test UI

Go full bling with detailed breakdowns for a power user like setup. stdout and
stderr, line numbers, code syntax highlighting, icons, error breakdowns etc.
Highly verbose, useful and a bit overwhelming for passing tests.

```sh
pip install -e .[dev,fancy]
```

## Development

### Testing PyPI README

Install the README renderer used by pypi.org itself

```
pip install "readme-renderer[md]"
```

Then run

```
python -m readme_renderer README.md -o index.html
```

### Releasing

Clear previous builds and build a new one

```
rm -rf dist
python -m build
```

Check the build

```
twine check dist/*
```

Upload to test PyPI first to catch any issues

```
twine upload --repository testpypi dist/*
```

Test install from test PyPI

```
pip uninstall anisodactyl
pip install --index-url https://test.pypi.org/simple/ anisodactyl
```

If test works, upload to real PyPI

```
twine upload --repository pypi dist/*
```

Git Tag and Push

```
git tag -a v0.1.0 -m "Initial release with core CRUD functionality"
git push origin v0.1.0
```
