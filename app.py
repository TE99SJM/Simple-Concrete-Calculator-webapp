from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "concrete-calculator-secret"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE = DATA_DIR / "concrete_calculator.db"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                section_number INTEGER NOT NULL,

                length REAL NOT NULL DEFAULT 0,
                width REAL NOT NULL DEFAULT 0,
                thickness REAL NOT NULL DEFAULT 0,

                result REAL NOT NULL DEFAULT 0,

                rebar_widthwise INTEGER NOT NULL DEFAULT 0,
                rebar_lengthwise INTEGER NOT NULL DEFAULT 0,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(customer_id, section_number),

                FOREIGN KEY(customer_id)
                    REFERENCES customers(id)
            )
        """)

        # ----------------------------------------------------
        # DATABASE MIGRATION
        #
        # These allow an existing Concrete Calculator database
        # to be upgraded without deleting customers/sections.
        # ----------------------------------------------------

        columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(sections)"
            ).fetchall()
        ]

        if "rebar_widthwise" not in columns:
            conn.execute("""
                ALTER TABLE sections
                ADD COLUMN rebar_widthwise INTEGER NOT NULL DEFAULT 0
            """)

        if "rebar_lengthwise" not in columns:
            conn.execute("""
                ALTER TABLE sections
                ADD COLUMN rebar_lengthwise INTEGER NOT NULL DEFAULT 0
            """)

        conn.commit()


# ============================================================
# CALCULATOR
# ============================================================

def calculate_concrete(length, width, thickness):

    """
    CONCRETE + REBAR CALCULATOR

    This function contains the calculation logic from the
    original Concrete Calculator Python program.

    INPUTS

    length:
        Concrete section length in feet.

    width:
        Concrete section width in feet.

    thickness:
        Concrete thickness in inches.


    OUTPUTS

    concrete:
        Cubic yards + 1 cubic yard.

    rebar_widthwise:
        Rebar quantity calculated from the length.

    rebar_lengthwise:
        Rebar quantity calculated from the width.
    """

    # --------------------------------------------------------
    # CONCRETE
    # --------------------------------------------------------

    # Convert feet to yards
    lyd = length / 3
    wyd = width / 3

    # Convert inches to yards
    tyd = thickness / 36

    # Cubic yards
    cuyd = lyd * wyd * tyd

    # Original calculator adds one cubic yard
    concrete = round(cuyd + 1, 1)


    # --------------------------------------------------------
    # REBAR
    #
    # Original calculator:
    #
    # rl = round(((L*12-30)/18),0)
    # wl = round(((W*12-30)/18),0)
    #
    # --------------------------------------------------------

    rebar_widthwise = round(
        ((length * 12 - 30) / 18),
        0
    )

    rebar_lengthwise = round(
        ((width * 12 - 30) / 18),
        0
    )


    # Don't allow negative rebar quantities
    rebar_widthwise = max(
        0,
        int(rebar_widthwise)
    )

    rebar_lengthwise = max(
        0,
        int(rebar_lengthwise)
    )


    return {
        "concrete": concrete,
        "rebar_widthwise": rebar_widthwise,
        "rebar_lengthwise": rebar_lengthwise
    }


# ============================================================
# CUSTOMER SUMMARY
# ============================================================

def get_customer_summary(conn, customer_id):

    sections = conn.execute("""
        SELECT *
        FROM sections
        WHERE customer_id = ?
        ORDER BY section_number
    """, (customer_id,)).fetchall()


    total_concrete = sum(
        section["result"]
        for section in sections
    )


    total_rebar_widthwise = sum(
        section["rebar_widthwise"]
        for section in sections
    )


    total_rebar_lengthwise = sum(
        section["rebar_lengthwise"]
        for section in sections
    )


    return {

        "section_count":
            len(sections),

        "total_result":
            round(total_concrete, 1),

        "total_rebar_widthwise":
            total_rebar_widthwise,

        "total_rebar_lengthwise":
            total_rebar_lengthwise
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    with get_db() as conn:

        customers = conn.execute("""
            SELECT *
            FROM customers
            ORDER BY name COLLATE NOCASE
        """).fetchall()


    if customers:

        return redirect(
            url_for(
                "customer",
                customer_id=customers[0]["id"]
            )
        )


    return redirect(
        url_for("new_customer")
    )


# ============================================================
# NEW CUSTOMER
# ============================================================

@app.route(
    "/customers/new",
    methods=["GET", "POST"]
)
def new_customer():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()


        if not name:

            flash(
                "Please enter a customer name."
            )

            return redirect(
                url_for("new_customer")
            )


        with get_db() as conn:

            cursor = conn.execute("""
                INSERT INTO customers (name)
                VALUES (?)
            """, (name,))


            customer_id = cursor.lastrowid

            conn.commit()


        return redirect(
            url_for(
                "customer",
                customer_id=customer_id
            )
        )


    with get_db() as conn:

        customers = conn.execute("""
            SELECT *
            FROM customers
            ORDER BY name COLLATE NOCASE
        """).fetchall()


    return render_template(
        "new_customer.html",
        customers=customers
    )


# ============================================================
# CUSTOMER PAGE
# ============================================================

@app.route(
    "/customers/<int:customer_id>"
)
def customer(customer_id):

    section_id = request.args.get(
        "section_id",
        type=int
    )


    with get_db() as conn:

        customer_row = conn.execute("""
            SELECT *
            FROM customers
            WHERE id = ?
        """, (customer_id,)).fetchone()


        if not customer_row:

            flash(
                "Customer not found."
            )

            return redirect(
                url_for("index")
            )


        customers = conn.execute("""
            SELECT *
            FROM customers
            ORDER BY name COLLATE NOCASE
        """).fetchall()


        sections = conn.execute("""
            SELECT *
            FROM sections
            WHERE customer_id = ?
            ORDER BY section_number
        """, (customer_id,)).fetchall()


        selected_section = None


        if section_id:

            selected_section = conn.execute("""
                SELECT *
                FROM sections
                WHERE id = ?
                AND customer_id = ?
            """, (
                section_id,
                customer_id
            )).fetchone()


        if selected_section is None and sections:

            selected_section = sections[0]


        summary = get_customer_summary(
            conn,
            customer_id
        )


    return render_template(
        "customer.html",

        customer=customer_row,

        customers=customers,

        sections=sections,

        selected_section=selected_section,

        summary=summary
    )


# ============================================================
# NEW SECTION
# ============================================================

@app.route(
    "/customers/<int:customer_id>/sections/new",
    methods=["POST"]
)
def new_section(customer_id):


    with get_db() as conn:

        customer_row = conn.execute("""
            SELECT id
            FROM customers
            WHERE id = ?
        """, (customer_id,)).fetchone()


        if not customer_row:

            flash(
                "Customer not found."
            )

            return redirect(
                url_for("index")
            )


        next_number = conn.execute("""
            SELECT
            COALESCE(
                MAX(section_number),
                0
            ) + 1

            FROM sections

            WHERE customer_id = ?
        """, (customer_id,)).fetchone()[0]


        cursor = conn.execute("""
            INSERT INTO sections (

                customer_id,
                section_number,

                length,
                width,
                thickness,

                result,

                rebar_widthwise,
                rebar_lengthwise
            )

            VALUES (
                ?,
                ?,
                0,
                0,
                0,
                0,
                0,
                0
            )
        """, (
            customer_id,
            next_number
        ))


        section_id = cursor.lastrowid

        conn.commit()


    return redirect(
        url_for(
            "customer",
            customer_id=customer_id,
            section_id=section_id
        )
    )


# ============================================================
# CALCULATE + SAVE SECTION
# ============================================================

@app.route(
    "/customers/<int:customer_id>/sections/<int:section_id>",
    methods=["POST"]
)
def save_section(
    customer_id,
    section_id
):


    try:

        length = float(
            request.form.get(
                "length",
                0
            ) or 0
        )


        width = float(
            request.form.get(
                "width",
                0
            ) or 0
        )


        thickness = float(
            request.form.get(
                "thickness",
                0
            ) or 0
        )


    except ValueError:

        flash(
            "Length, width, and thickness must be valid numbers."
        )

        return redirect(
            url_for(
                "customer",
                customer_id=customer_id,
                section_id=section_id
            )
        )


    # --------------------------------------------------------
    # RUN CALCULATOR
    # --------------------------------------------------------

    calculation = calculate_concrete(
        length,
        width,
        thickness
    )


    concrete = calculation[
        "concrete"
    ]

    rebar_widthwise = calculation[
        "rebar_widthwise"
    ]

    rebar_lengthwise = calculation[
        "rebar_lengthwise"
    ]


    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    with get_db() as conn:


        section = conn.execute("""
            SELECT id
            FROM sections
            WHERE id = ?
            AND customer_id = ?
        """, (
            section_id,
            customer_id
        )).fetchone()


        if not section:

            flash(
                "Section not found."
            )

            return redirect(
                url_for(
                    "customer",
                    customer_id=customer_id
                )
            )


        conn.execute("""
            UPDATE sections

            SET

                length = ?,
                width = ?,
                thickness = ?,

                result = ?,

                rebar_widthwise = ?,
                rebar_lengthwise = ?,

                updated_at =
                    CURRENT_TIMESTAMP

            WHERE id = ?
        """, (

            length,
            width,
            thickness,

            concrete,

            rebar_widthwise,
            rebar_lengthwise,

            section_id
        ))


        conn.commit()


    flash(
        "Section calculated and saved."
    )


    return redirect(
        url_for(
            "customer",
            customer_id=customer_id,
            section_id=section_id
        )
    )


# ============================================================
# START APPLICATION
# ============================================================

init_db()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=3010,
        debug=False
    )
