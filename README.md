## Requirements

- [uv](https://docs.astral.sh/uv/)
- make
- [docker](https://www.docker.com/)

## Setup

After installing all requirements run this command to initialize the repo:

```bash
make install
```

## Run

Deploy services with docker using this command:

```bash
make deploy-local
```

To run the server run this command

```bash
make run
```

## Test

Run this command to execute tests.

**NOTE**: Ensure services are running before executing this command.

```bash
make test
```
