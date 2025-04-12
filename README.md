## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- make
- [docker](https://docs.docker.com/engine/install/)
- [infisical](https://infisical.com/docs/cli/overview)

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

To run the development server run this command

```bash
make run-dev
```

To run the development worker run this command

```bash
make worker-dev
```

## Test

Run this command to execute tests.

**NOTE**: Ensure services are running before executing this command.

```bash
make test
```
