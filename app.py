from dotenv import load_dotenv
import streamlit as st
import os
import mysql.connector
import pandas as pd
import google.generativeai as genai
import sqlite3
import psycopg2
from sqlalchemy import create_engine
import traceback

# Configuration
load_dotenv()
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ GOOGLE_API_KEY not found in .env file")
        st.stop()
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error loading configuration: {str(e)}")
    st.stop()

# Test Database Connection
def test_db_connection(db_type, host, user, password, database, port=None):
    try:
        if db_type == "MySQL":
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port or 3306
            )
            conn.close()
            return True, "✅ Successfully connected to MySQL database"
        elif db_type == "PostgreSQL":
            conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port or 5432
            )
            conn.close()
            return True, "✅ Successfully connected to PostgreSQL database"
        elif db_type == "SQLite":
            if not os.path.exists(database):
                return False, "❌ SQLite database file not found"
            conn = sqlite3.connect(database)
            conn.close()
            return True, "✅ Successfully connected to SQLite database"
        else:
            return False, f"❌ Unsupported database type: {db_type}"
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            return False, "❌ Access denied. Please check your username and password"
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            return False, f"❌ Database '{database}' does not exist"
        else:
            return False, f"❌ MySQL Error: {str(err)}"
    except psycopg2.Error as err:
        return False, f"❌ PostgreSQL Error: {str(err)}"
    except sqlite3.Error as err:
        return False, f"❌ SQLite Error: {str(err)}"
    except Exception as err:
        return False, f"❌ Unexpected error: {str(err)}"

# Database Connection
def get_db_connection(db_type, host, user, password, database, port=None):
    try:
        if db_type == "MySQL":
            return mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port or 3306
            )
        elif db_type == "PostgreSQL":
            return psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port or 5432
            )
        elif db_type == "SQLite":
            if not os.path.exists(database):
                raise FileNotFoundError(f"SQLite database file not found: {database}")
            return sqlite3.connect(database)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            st.error("❌ Database access denied. Please check your username and password.")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            st.error(f"❌ Database '{database}' does not exist.")
        else:
            st.error(f"❌ MySQL Error: {str(err)}")
        st.stop()
    except psycopg2.Error as err:
        st.error(f"❌ PostgreSQL Error: {str(err)}")
        st.stop()
    except sqlite3.Error as err:
        st.error(f"❌ SQLite Error: {str(err)}")
        st.stop()
    except Exception as err:
        st.error(f"❌ Unexpected error during database connection: {str(err)}")
        st.stop()

# AI Response Generation
def get_gemini_response(question, prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content([prompt[0], question])
        if not response.text:
            raise ValueError("Empty response from AI model")
        return response.text
    except Exception as e:
        st.error(f"❌ AI Error: {str(e)}")
        st.error("Please check if your Google API key is valid and has sufficient quota.")
        st.stop()

# Query Execution
def execute_sql_query(sql_query, db_type, host, user, password, database, port=None):
    sql_query = sql_query.strip().strip("```sql").strip("```")
    
    try:
        conn = get_db_connection(db_type, host, user, password, database, port)
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql_query)
        except Exception as e:
            st.error(f"❌ SQL Query Error: {str(e)}")
            st.error("Please check your SQL query syntax and table structure.")
            return None, None
        
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return columns, rows
        return None, None
        
    except Exception as err:
        st.error(f"❌ Database Error: {str(err)}")
        return None, None
    finally:
        try:
            if hasattr(conn, 'close'):
                cursor.close()
                conn.close()
        except Exception as e:
            st.warning(f"⚠️ Warning: Error while closing database connection: {str(e)}")

# --- Streamlit UI ---
def main():
    st.set_page_config(page_icon="icons8-database.gif", page_title="Text-to-SQL Query Tool", layout="wide")
    st.title("📊 Text-to-SQL Query Tool")
    
    # Initialize session state for database connection
    if 'db_connected' not in st.session_state:
        st.session_state.db_connected = False
    if 'db_config' not in st.session_state:
        st.session_state.db_config = {}
    
    # Database Connection Settings
    with st.sidebar:
        st.title("📊 Text-to-SQL Query Tool")
        st.header("Database Settings")
        try:
            db_type = st.selectbox(
                "Database Type *",
                ["MySQL", "PostgreSQL", "SQLite"],
                index=0
            )
            
            if db_type != "SQLite":
                db_host = st.text_input("Host *", value="localhost")
                db_user = st.text_input("Username *", value="root")
                db_password = st.text_input("Password *", type="password")
                db_port = st.number_input("Port *", min_value=1, max_value=65535, 
                                        value=3306 if db_type == "MySQL" else 5432)
            
            if db_type == "SQLite":
                db_path = st.text_input("Database File Path *")
            else:
                db_name = st.text_input("Database Name *")
            
            # Add a submit button for database settings
            if st.button("Connect to Database", type="primary"):
                # Validate required fields
                if db_type == "SQLite":
                    if not db_path:
                        st.error("❌ Database file path is required")
                    else:
                        # Test connection
                        success, message = test_db_connection(db_type, None, None, None, db_path)
                        if success:
                            st.session_state.db_config = {
                                "type": db_type,
                                "path": db_path
                            }
                            st.session_state.db_connected = True
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    if not all([db_host, db_user, db_password, db_name]):
                        st.error("❌ All fields are required")
                    else:
                        # Test connection
                        success, message = test_db_connection(db_type, db_host, db_user, db_password, db_name, db_port)
                        if success:
                            st.session_state.db_config = {
                                "type": db_type,
                                "host": db_host,
                                "user": db_user,
                                "password": db_password,
                                "database": db_name,
                                "port": db_port
                            }
                            st.session_state.db_connected = True
                            st.success(message)
                        else:
                            st.error(message)
        except Exception as e:
            st.error(f"❌ Error in database settings UI: {str(e)}")
            st.stop()
    
    # Only show the query interface if database is connected
    if not st.session_state.db_connected:
        st.warning("⚠️ Please configure and connect to your database first")
        return
    
    prompt = [
        """You are a healthcare SQL expert. Database schema:
        PATIENTS (patient_id, first_name, last_name, dob, gender, phone, insurance_id)
        DOCTORS (doctor_id, first_name, last_name, specialization, department_id, license_number, phone)
        DEPARTMENTS (department_id, name, head_doctor_id)
        APPOINTMENTS (appointment_id, patient_id, doctor_id, appointment_date, status)
        MEDICAL_RECORDS (record_id, patient_id, doctor_id, diagnosis, prescription, record_date)
        LAB_RESULTS (lab_id, patient_id, test_name, test_date, result_value, reference_range)
        
        Rules:
        1. Use explicit JOIN syntax
        2. Format dates using DATE_FORMAT()
        3. Always qualify column names with table aliases
        4. Include relevant WHERE clauses
        5. Handle NULL values appropriately"""
    ]
    
    try:
        question = st.text_area("Enter your healthcare data question:", 
                              placeholder="e.g., Show patients with cholesterol levels above 200 mg/dL",
                              height=100)
        
        if st.button("Analyze Data"):
            if not question:
                st.warning("⚠️ Please enter a question")
                return
                
            with st.spinner("🔍 Analyzing data..."):
                try:
                    # Generate and execute query
                    sql = get_gemini_response(question, prompt)
                    
                    # Prepare database parameters based on type
                    if st.session_state.db_config["type"] == "SQLite":
                        columns, data = execute_sql_query(sql, 
                                                        st.session_state.db_config["type"],
                                                        None, None, None, 
                                                        st.session_state.db_config["path"])
                    else:
                        columns, data = execute_sql_query(sql, 
                                                        st.session_state.db_config["type"],
                                                        st.session_state.db_config["host"],
                                                        st.session_state.db_config["user"],
                                                        st.session_state.db_config["password"],
                                                        st.session_state.db_config["database"],
                                                        st.session_state.db_config["port"])
                    
                    # Display results
                    st.subheader("Generated SQL Query")
                    st.code(sql, language="sql")
                    
                    if columns and data:
                        st.subheader("Analysis Results")
                        df = pd.DataFrame(data, columns=columns)
                        st.dataframe(df, use_container_width=True)
                        
                        # Basic visualizations
                        if len(df) > 0:
                            numeric_cols = df.select_dtypes(include=['number']).columns
                            if not numeric_cols.empty:
                                selected_col = st.selectbox("Select column to visualize:", numeric_cols)
                                st.line_chart(df[selected_col])
                    else:
                        st.info("ℹ️ No results found for this query")
                        
                except Exception as e:
                    st.error(f"❌ Error processing request: {str(e)}")
                    st.error("Stack trace:")
                    st.code(traceback.format_exc())
    except Exception as e:
        st.error(f"❌ Error in main UI: {str(e)}")
        st.error("Stack trace:")
        st.code(traceback.format_exc())
    
    # Sample questions sidebar
    with st.sidebar:
        st.markdown("### 💡 Sample Questions")
        st.write("- List patients with cholesterol above 200 mg/dL")
        st.write("- Show average lab results by test type")
        st.write("- Find doctors with most appointments this month")
        st.write("- Patients with multiple prescriptions in March 2024")
        st.write("- Upcoming appointments for cardiology department")

if __name__ == "__main__":
    main()
