# Concrete Calculator

A Dockerized Flask web application for storing customers, storing multiple concrete sections per customer, and calculating concrete quantities.

The application runs on **port 3010** and stores its SQLite database in a persistent Docker volume.

## Features

- Multiple customers
- Create a new customer
- Select an existing customer
- Multiple concrete sections per customer
- Automatically incrementing section numbers
- Section dropdown and section list
- Persistent customer summary while switching sections
- Responsive layout for desktop and iPhone
- SQLite database initialized automatically
- Persistent Docker storage
- All calculation logic isolated in one Python function
- Ready for your existing calculation code to be pasted in later

## Project Structure

```text
Concrete Calculator/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── README.md
├── data/
│   └── .gitkeep
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── customer.html
    └── new_customer.html
```

## Requirements

Install Docker and Docker Compose on the server.

Verify:

```bash
docker --version
docker compose version
```

## First-Time Setup

### 1. Copy the project to your server

Move the entire `Concrete Calculator` folder to the server.

Example:

```bash
cd /path/to/Concrete\ Calculator
```

### 2. Build and start the application

From inside the project folder, run:

```bash
docker compose up -d --build
```

### 3. Open the application

On the server itself:

```text
http://localhost:3010
```

From another device on the same network:

```text
http://SERVER-IP:3010
```

Example:

```text
http://192.168.1.100:3010
```

## Start

```bash
docker compose up -d
```

## Stop

```bash
docker compose down
```

Stopping or recreating the container does **not** delete customer data because the database is stored in a Docker volume.

## Restart

```bash
docker compose restart
```

## View Logs

```bash
docker compose logs -f
```

Press `Ctrl+C` to stop following the logs.

## Update the Application

If you change Python, HTML, CSS, Docker configuration, or requirements, rebuild the container:

```bash
docker compose down
docker compose up -d --build
```

Your SQLite data will remain intact.

## Data Persistence

The application uses the Docker named volume:

```text
concrete_calculator_data
```

It is mounted inside the container at:

```text
/app/data
```

The SQLite database is:

```text
/app/data/concrete_calculator.db
```

The normal command:

```bash
docker compose down
```

does not remove the volume.

### Important

Do **not** run the following unless you intentionally want to delete the saved database:

```bash
docker compose down -v
```

The `-v` option removes the named volume.

## Backup the Database

To find the Docker volume:

```bash
docker volume ls
```

A simple backup can also be made by copying the database file from the running container:

```bash
docker cp concrete-calculator:/app/data/concrete_calculator.db ./concrete_calculator_backup.db
```

## Restore a Database Backup

Stop the app:

```bash
docker compose down
```

Start the container again:

```bash
docker compose up -d
```

Copy the backup into the container:

```bash
docker cp concrete_calculator_backup.db concrete-calculator:/app/data/concrete_calculator.db
```

Restart:

```bash
docker compose restart
```

## Replacing the Placeholder Calculation With Your Own Python Code

All calculation logic is intentionally isolated in a single function in:

```text
app.py
```

Find this function:

```python
def calculate_concrete(length, width, thickness):
```

The current placeholder code is:

```python
cubic_feet = length * width * (thickness / 12.0)
cubic_yards = cubic_feet / 27.0
return round(cubic_yards, 3)
```

### Step 1: Keep the function name

Leave this line in place:

```python
def calculate_concrete(length, width, thickness):
```

The rest of the application calls that exact function.

### Step 2: Replace only the calculation inside the function

For example:

```python
def calculate_concrete(length, width, thickness):
    # Paste or adapt your calculation here.
    result = length * width * thickness
    return result
```

### Step 3: Add additional inputs if your existing calculator needs them

If your calculation needs more values than `length`, `width`, and `thickness`, you will need to make three matching changes:

1. Add fields to the `sections` table in `init_db()`.
2. Add form fields in `templates/customer.html`.
3. Read those values in the `save_section()` route and pass them into `calculate_concrete()`.

For example:

```python
def calculate_concrete(length, width, thickness, waste_percent):
```

Then update the call:

```python
result = calculate_concrete(length, width, thickness, waste_percent)
```

### Step 4: Make sure the function returns a number

The current application stores the returned result in SQLite.

A valid return value might be:

```python
return 4.25
```

Avoid returning formatted text such as:

```python
return "4.25 cubic yards"
```

Store the number and let the interface add the unit.

### Step 5: Rebuild after changing the Python code

Run:

```bash
docker compose down
docker compose up -d --build
```

### Step 6: Test the calculator

Open:

```text
http://SERVER-IP:3010
```

Create a test customer, add a section, enter measurements, and click:

```text
Calculate & Save
```

## Changing the Port

The application is currently configured for port `3010`.

In `docker-compose.yml`:

```yaml
ports:
  - "3010:3010"
```

The left number is the server port.

For example, to expose it on port 3050 while leaving the internal container port unchanged:

```yaml
ports:
  - "3050:3010"
```

You would then open:

```text
http://SERVER-IP:3050
```

## Database Tables

### customers

Stores:

- customer ID
- customer name
- creation timestamp

### sections

Stores:

- section ID
- customer ID
- automatically assigned section number
- length
- width
- thickness
- calculation result
- creation timestamp
- update timestamp

Each customer has its own section numbering sequence beginning with Section 1.

## Notes

The Flask application automatically initializes the database tables when the app starts.

No manual database setup command is required.

The default calculation is intentionally simple so it can be replaced later without restructuring the entire application.


## Integrated Calculator Logic

The placeholder formula has been replaced with the supplied Python calculator logic. The web app now calculates:

```python
lyd = length / 3
wyd = width / 3
tyd = thickness / 36
cuyd = lyd * wyd * tyd
cy = round(cuyd + 1, 1)
return cy
```

This preserves the original behavior: calculate cubic yards, add 1 cubic yard, then round to one decimal place. Customer-name entry from the command-line script is handled by the web application's customer selector/database. The unused `tkinter` and `numpy` imports from the original script are not needed in the Flask app.
