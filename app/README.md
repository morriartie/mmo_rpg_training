# First time setup

```bash
make build
make migrate
```

# Running the application

```bash
make run
```

# Common tasks
## Access logs

```bash
make logs
```

## Run a shell in container

```bash
make shell
```

## Format code

```bash
make format
```

## Lint code

```bash
make lint
```

## Clean up

```bash
make clean
```

# Testing API
## Create account

```bash
curl -X POST http://localhost:8000/account/testuser
```

## Create character

```bash
curl -X POST http://localhost:8000/character?userid=testuser&charname=warrior
```

## Login (replace 1 with actual character ID)

```bash
curl -X POST http://localhost:8000/login/1
```

## Move character

```bash
curl -X POST http://localhost:8000/move/1?dx=1.0&dy=0.5
```

## Attack target (replace 2 with target ID)

```bash
curl -X POST http://localhost:8000/attack/1?target_id=2
```

## Stream game events

```bash
curl -N http://localhost:8000/events
```

# Sample Run
## Build and run normally:

```bash
make run
```

## Populate database manually:

```bash
make populate-docker
```

## Or run with pre-populated data:

```bash
make run-populated
```

