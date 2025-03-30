# Text-to-SQL-Query-Tool

This is a Streamlit-based web application that allows users to generate SQL queries from natural language input using Facebook OPT models. It supports connections to multiple database types and enables query execution and schema exploration.

## Features

- Natural Language to SQL Conversion: Converts user queries into SQL statements using Transformer models.

- Database Connectivity: Supports SQLite, MySQL, PostgreSQL, and MS SQL Server.

- Schema Inspection: Fetches and displays database schema information.

- Query Execution: Runs the generated SQL queries and displays results.

- Interactive Chat Interface: Enables a chat-based experience for asking database-related questions.


## Requirements

### Dependencies

Ensure you have the following Python packages installed:

```python
pip install streamlit transformers sqlalchemy pandas torch python-dotenv pymysql pyodbc
```

### Environment Variables

Create a `.env` file (optional) for storing sensitive database credentials.

## Installation & Usage

### Clone the Repository

```python
git clone https://github.com/tamaraiselva/Text-to-SQL-Query-Tool.git
cd Text-to-SQL-Query-Tool
```

## Run the Application

```py
streamlit run app.py
```

## Configuration

### Model Selection

The application supports multiple OPT models:

- `facebook/opt-125m (default)`

- `facebook/opt-350m`

- `facebook/opt-1.3b`

You can select the model from the sidebar.

### Database Connection

Configure the database connection via the sidebar by selecting the Database Type and providing necessary credentials.

## Usage Guide

1. Connect to a Database via the sidebar.

2. View Schema in the "Database Schema" tab.

3. Ask Questions in the chat interface to generate SQL.

4. Execute Queries to see results.

## Acknowledgments

1. Facebook OPT Models for NLP processing.

2. Streamlit for UI development.

3. SQLAlchemy for database interaction.

## License

This project is licensed under the `MIT` License.
