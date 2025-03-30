import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import torch
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
DEFAULT_MODEL = "facebook/opt-125m"  # Smaller, publicly available model
DB_TYPES = {
    "SQLite": "sqlite",
    "MySQL": "mysql+pymysql",
    "PostgreSQL": "postgresql",
    "MS SQL Server": "mssql+pyodbc"
}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db_engine" not in st.session_state:
    st.session_state.db_engine = None
if "db_schema" not in st.session_state:
    st.session_state.db_schema = {}

# --- Model Loading (CPU-compatible) ---
@st.cache_resource
def load_model(model_name=DEFAULT_MODEL):
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",  # Force CPU
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32  # Optimize for CPU
        )
        return tokenizer, model
    except Exception as e:
        st.error(f"Failed to load model: {str(e)}")
        return None, None

# --- SQL Generation (CPU-compatible) ---
def generate_sql(tokenizer, model, prompt, max_length=300):
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to("cpu")  # Force CPU
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True
        )
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        st.error(f"Error during SQL generation: {str(e)}")
        return None

# --- Database Functions ---
def create_db_connection(db_type, host, port, database, username, password):
    try:
        if db_type == "SQLite":
            connection_string = f"sqlite:///{database}"
        else:
            connection_string = f"{DB_TYPES[db_type]}://{username}:{password}@{host}:{port}/{database}"
        
        engine = create_engine(connection_string)
        st.session_state.db_engine = engine
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

def get_db_schema(engine):
    inspector = inspect(engine)
    schema = {}
    
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "primary_key": column.get("primary_key", False)
            })
        
        schema[table_name] = {
            "columns": columns,
            "primary_key": inspector.get_pk_constraint(table_name).get("constrained_columns", [])
        }
    
    st.session_state.db_schema = schema
    return schema

def format_schema_for_prompt(schema):
    prompt = "Database schema:\n"
    for table_name, table_info in schema.items():
        prompt += f"- Table {table_name}:\n"
        for column in table_info["columns"]:
            prompt += f"  - {column['name']} ({column['type']})"
            if column["primary_key"]:
                prompt += " (PRIMARY KEY)"
            prompt += "\n"
        if table_info["primary_key"]:
            prompt += f"  Primary key: {', '.join(table_info['primary_key'])}\n"
    return prompt

def execute_query(engine, query_str):
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query_str))
            if result.returns_rows:
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df
            else:
                return f"Query executed successfully. Rows affected: {result.rowcount}"
    except SQLAlchemyError as e:
        return f"Error executing query: {str(e)}"

# --- Streamlit UI ---
st.set_page_config(page_title="Text-to-SQL Query Tool", layout="wide")
st.title("📊 Text-to-SQL Query Tool")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Model selection
    model_option = st.selectbox(
        "Select Model",
        ["facebook/opt-125m", "facebook/opt-350m", "facebook/opt-1.3b"],
        index=0
    )
    
    # Database connection
    st.subheader("Database Connection")
    db_type = st.selectbox("Database Type", list(DB_TYPES.keys()), index=0)
    
    if db_type != "SQLite":
        col1, col2 = st.columns(2)
        host = col1.text_input("Host", "localhost")
        port = col2.text_input("Port", "3306" if db_type == "MySQL" else "5432")
        database = st.text_input("Database Name", "mydatabase")
        username = st.text_input("Username", "root")
        password = st.text_input("Password", type="password")
    else:
        database = st.text_input("Database File Path", "example.db")
        host, port, username, password = "", "", "", ""
    
    if st.button("Connect to Database"):
        with st.spinner("Connecting..."):
            engine = create_db_connection(db_type, host, port, database, username, password)
            if engine:
                st.success("Connected successfully!")
                get_db_schema(engine)
            else:
                st.error("Connection failed")

# Main interface
tab1, tab2 = st.tabs(["Query", "Database Schema"])

with tab1:
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask a question about your data"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            if st.session_state.db_engine is None:
                full_response = "⚠️ Please connect to a database first."
            else:
                # Prepare the prompt with schema
                schema_prompt = format_schema_for_prompt(st.session_state.db_schema)
                full_prompt = f"{schema_prompt}\n\nQuestion: {prompt}\n\nSQL Query:"
                
                # Load model if not already loaded
                if "tokenizer" not in st.session_state or "model" not in st.session_state:
                    with st.spinner("Loading model..."):
                        st.session_state.tokenizer, st.session_state.model = load_model(model_option)
                
                # Generate SQL
                with st.spinner("Generating SQL query..."):
                    sql_query = generate_sql(
                        st.session_state.tokenizer,
                        st.session_state.model,
                        full_prompt
                    )
                
                if sql_query:
                    full_response += f"```sql\n{sql_query}\n```"
                    
                    # Execute the query
                    with st.spinner("Executing query..."):
                        result = execute_query(st.session_state.db_engine, sql_query)
                    
                    if isinstance(result, pd.DataFrame):
                        full_response += "\n\n**Query Results:**"
                        st.dataframe(result)
                    else:
                        full_response += f"\n\n**Execution Result:** {result}"
                else:
                    full_response = "Failed to generate SQL query."
            
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

with tab2:
    if st.session_state.db_engine:
        st.subheader("Database Schema Information")
        
        if st.session_state.db_schema:
            for table_name, table_info in st.session_state.db_schema.items():
                with st.expander(f"Table: {table_name}"):
                    st.write("Columns:")
                    cols = st.columns(3)
                    for i, column in enumerate(table_info["columns"]):
                        col_idx = i % 3
                        cols[col_idx].code(f"{column['name']}: {column['type']}")
                    
                    if table_info["primary_key"]:
                        st.write(f"Primary key: {', '.join(table_info['primary_key'])}")
        else:
            st.warning("No schema information available. Please connect to a database.")
    else:
        st.warning("No database connected. Please configure the connection in the sidebar.")