import os
import pandas as pd
import mysql.connector
from llama_cpp import Llama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# === CONFIGURATION ===
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "sakila",
    "user": "root",
    "password": "acces123"
}

MODEL_PATH = "./mistral-7b-instruct-v0.2.Q4_K_M.gguf"
N_CTX = 4096

# === LOAD LOCAL LLAMA MODEL ===
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=N_CTX,
    n_threads=6,
    n_gpu_layers=20,
    verbose=False
)

# === FASTAPI APP ===
app = FastAPI()
app.add_middleware(
    
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

# === GENERATE SQL FROM QUESTION ===
def generate_sql(question: str) -> str:
    schema = """
SCHEMA OF SAKILA DATABASE:

Table: actor (a)
- actor_id (SMALLINT, PK)
- first_name (VARCHAR(45))
- last_name (VARCHAR(45))
- last_update (TIMESTAMP)

Table: address (ad)
- address_id (SMALLINT, PK)
- address (VARCHAR(50))
- address2 (VARCHAR(50), NULLABLE)
- district (VARCHAR(20))
- city_id (SMALLINT)
- postal_code (VARCHAR(10), NULLABLE)
- phone (VARCHAR(20))
- location (GEOMETRY)
- last_update (TIMESTAMP)

Table: category (c)
- category_id (TINYINT, PK)
- name (VARCHAR(25))
- last_update (TIMESTAMP)

Table: city (ci)
- city_id (SMALLINT, PK)
- city (VARCHAR(50))
- country_id (SMALLINT)
- last_update (TIMESTAMP)

Table: country (co)
- country_id (SMALLINT, PK)
- country (VARCHAR(50))
- last_update (TIMESTAMP)

Table: customer (cu)
- customer_id (SMALLINT, PK)
- store_id (TINYINT)
- first_name (VARCHAR(45))
- last_name (VARCHAR(45))
- email (VARCHAR(50))
- address_id (SMALLINT)
- active (TINYINT, DEFAULT '1')
- create_date (DATETIME)
- last_update (TIMESTAMP)

Table: film (f)
- film_id (INT, PK)
- title (VARCHAR(255))
- description (TEXT)
- release_year (YEAR)
- language_id (INT)
- original_language_id (INT, NULLABLE)
- rental_duration (INT)
- rental_rate (DECIMAL)
- length (INT)
- replacement_cost (DECIMAL)
- rating (VARCHAR(10))
- special_features (VARCHAR(255))
- last_update (DATETIME)

Table: film_actor (fa)
- actor_id (SMALLINT, PK)
- film_id (SMALLINT, PK)
- last_update (TIMESTAMP)

Table: film_category (fc)
- film_id (SMALLINT, PK)
- category_id (TINYINT, PK)
- last_update (TIMESTAMP)

Table: film_text (ft)
- film_id (SMALLINT, PK)
- title (VARCHAR(255))
- description (TEXT)

Table: inventory (i)
- inventory_id (MEDIUMINT, PK)
- film_id (SMALLINT)
- store_id (TINYINT)
- last_update (TIMESTAMP)

Table: language (l)
- language_id (TINYINT, PK)
- name (CHAR(20))
- last_update (TIMESTAMP)

Table: payment (p)
- payment_id (SMALLINT, PK)
- customer_id (SMALLINT)
- staff_id (TINYINT)
- rental_id (INT)
- amount (DECIMAL(5,2))
- payment_date (DATETIME)

Table: rental (r)
- rental_id (INT, PK)
- rental_date (DATETIME)
- inventory_id (MEDIUMINT)
- customer_id (SMALLINT)
- return_date (DATETIME)
- staff_id (TINYINT)
- last_update (TIMESTAMP)

Table: staff (s)
- staff_id (TINYINT, PK)
- first_name (VARCHAR(45))
- last_name (VARCHAR(45))
- address_id (SMALLINT)
- picture (BLOB)
- email (VARCHAR(50))
- store_id (TINYINT)
- active (TINYINT)
- username (VARCHAR(16))
- password (VARCHAR(40))
- last_update (TIMESTAMP)

Table: store (st)
- store_id (TINYINT, PK)
- manager_staff_id (TINYINT)
- address_id (SMALLINT)
- last_update (TIMESTAMP)
"""

    prompt = f"""
You are an expert SQL generator for the Sakila MySQL database.

### TASK:
Generate ONLY one syntactically correct SQL query for the user's question.

### RULES:
- DO NOT include explanations, translations, markdown, or any labels like 'Answer:'.
- Use table aliases (e.g., film AS f, category AS c, film_category AS fc, actor AS a, film_actor AS fa).
- Use ONLY tables and columns from the schema below.
- Do NOT output explanations, markdown, or comments. Only the SQL query.
- All string comparisons must be case-insensitive (use LOWER()).
- If a column exists in multiple tables, specify the table alias.
- If you use category data (like c.name), you MUST JOIN: film -> film_category -> category.
- If you use actor data, you MUST JOIN: actor -> film_actor -> film.
- For customer addresses, JOIN: customer -> address -> city.
- For inventory, JOIN: film -> inventory.
- Generate ONE single SQL query that answers the question.
- Do NOT generate multiple options or alternatives.
- Do NOT use UNION unless explicitly required by the question.
- Do NOT output "OR SELECT", "Option 1", "Option 2" or any alternatives.
- If the user's question is unrelated to the Sakila database (e.g., greetings, thanks, nonsense), respond with exactly:
NO_SQL_QUERY_POSSIBLE

### SCHEMA:

{schema}

### USER QUESTION:
"{question}"
"""

    output = llm(prompt=prompt, max_tokens=512, stop=["</s>"])
    raw_output = output["choices"][0]["text"].strip()


    # Curățare SQL: elimină explicații sau markdown
    lines = raw_output.splitlines()
    cleaned_sql = "\n".join([
        line for line in lines
        if not line.strip().lower().startswith(("translation", "explanation", "answer", "sql"))
        and not line.strip().startswith("```")
    ])

    upper_sql = cleaned_sql.upper()
    if "OR SELECT" in upper_sql or "OPTION" in upper_sql:
        raise ValueError("Invalid SQL: Detected multiple options or 'OR SELECT'.")

    return cleaned_sql.strip()

# === RUN SQL ===
def run_sql_query(query: str):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colnames)
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        return f"SQL Error: {e}"

# === GENERATE NATURAL LANGUAGE ANSWER ===
def generate_answer(question: str, data: pd.DataFrame) -> str:
    if isinstance(data, str):
        return data  # return error message

    table_str = data.to_markdown(index=False)

    prompt = f"""
You are a helpful assistant. Answer the user's question using the following data.

Question: {question}

Data:
{table_str}

Answer in natural language:
"""
    output = llm(prompt=prompt, max_tokens=300, stop=["</s>"])
    return output["choices"][0]["text"].strip()

# === API ===
@app.post("/ask")
def ask(req: QuestionRequest):
    try:
        sql_query = generate_sql(req.question)
        result = run_sql_query(sql_query)
        answer = generate_answer(req.question, result)

        return {
            "sql": sql_query,
            "result": result.to_dict(orient="records") if isinstance(result, pd.DataFrame) else result,
            "answer": answer
        }
    except Exception as e:
        return {"error": str(e)}

# === CONSOLE MODE ===
def console_mode():
    print("🎧 Welcome to the Sakila AI Database Assistant (Console Mode)")
    while True:
        user_input = input("Ask a question (or type 'exit'): ")
        if user_input.lower() == "exit":
            break

        sql_query = generate_sql(user_input)
        print(f"\n🔍 SQL Query:\n{sql_query}\n")

        result = run_sql_query(sql_query)

        if isinstance(result, str):
            print(result)
            continue

        print("📊 Query Result:")
        print(result.to_string(index=False))

        print("\n🤖 AI Answer:")
        response = generate_answer(user_input, result)
        print(response + "\n")

if __name__ == "__main__":
    console_mode()
