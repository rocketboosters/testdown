# Extraction Scenario

A scenario that demonstrates named code block extraction across multiple common
block types, as used in real-world markdown-driven test suites like those in the
`example/` directory.

## Setup

Executable setup code block defining the test configuration:

```python setup
environment = "test"
version = 1
greeting = "hello"
```

## Configuration

JSON-encoded configuration data for comparison assertions:

```json config
{ "environment": "test", "version": 1 }
```

## Metadata

YAML-encoded metadata block:

```yaml metadata
name: extraction
enabled: true
tags:
  - integration
  - scenario
```

## Source Data

Tabular CSV data for frame conversion testing:

```csv population
name,score
Alice,95
Bob,87
Carol,72
```

## Expected Results

Blocks following the `expected_<category>_<metric>` naming convention mirror the
real-world pattern used in parametrized population tests:

```json expected_config_environment
{ "environment": "test" }
```

```json expected_config_version
{ "version": 1 }
```
