# Discohook bot

Helper bot for Discohook.

Invite using <https://discord.com/api/oauth2/authorize?client_id=633565743103082527&permissions=537250880&scope=bot>.

## Installing

Requires Python 3.8

```sh
python3.8 -m venv venv  # Create virtual environment
source venv/bin/activate  # Activate virtual environment
pip install -Ur requirements.txt  # Install dependencies
```

This project requires a postgres database, migrations are done with `agnostic`.

Create a role and a database.

```sql
CREATE ROLE discohookbot WITH LOGIN PASSWORD 'secure-password';
CREATE DATABASE discohookbot;
GRANT ALL ON DATABASE discohookbot TO discohookbot;
```

Bootstrap agnostic and migrate to the lastest database version.

```sh
agnostic -t postgres -u discohookbot -d discohookbot bootstrap --no-load-existing
agnostic -t postgres -u discohookbot -d discohookbot migrate
```

## Running

Make sure that the virtual environment is active.

Load configuration using environment variables, or using a `.env` file.

Relevant environment variables are:

- `DISCORD_TOKEN`: Discord bot token
- `DATABASE_DSN`: Database credentials in the form of the [libpq connection URI format](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)

Once configured, the bot can be started using the following command:

```sh
python main.py
```
