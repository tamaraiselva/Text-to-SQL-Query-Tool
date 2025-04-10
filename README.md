# Text-to-SQL Query Tool

A Streamlit-based application that converts natural language questions into SQL queries and executes them against various database types.

## Features

- 🤖 Natural Language to SQL conversion using Google's Gemini AI
- 🔌 Support for multiple database types:
  - MySQL
  - PostgreSQL
  - SQLite
- 📊 Interactive data visualization
- 🔒 Secure database connection handling
- ⚡ Real-time query execution
- 📝 Sample questions for healthcare data analysis

## Prerequisites

- Python 3.8+
- MySQL/PostgreSQL/SQLite database
- Google API key for Gemini AI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Text-to-SQL-Query-Tool.git
cd Text-to-SQL-Query-Tool
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_api_key_here
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Configure database connection:
   - Select database type
   - Enter connection details
   - Click "Connect to Database"

3. Enter your question in natural language
4. Click "Analyze Data" to execute the query

## Database Schema

The application is pre-configured for healthcare data with the following schema:

```sql
PATIENTS (patient_id, first_name, last_name, dob, gender, phone, insurance_id)
DOCTORS (doctor_id, first_name, last_name, specialization, department_id, license_number, phone)
DEPARTMENTS (department_id, name, head_doctor_id)
APPOINTMENTS (appointment_id, patient_id, doctor_id, appointment_date, status)
MEDICAL_RECORDS (record_id, patient_id, doctor_id, diagnosis, prescription, record_date)
LAB_RESULTS (lab_id, patient_id, test_name, test_date, result_value, reference_range)
```

## Sample Questions

- List patients with cholesterol above 200 mg/dL
- Show average lab results by test type
- Find doctors with most appointments this month
- Patients with multiple prescriptions in March 2024
- Upcoming appointments for cardiology department

## Error Handling

The application includes comprehensive error handling for:
- Database connection issues
- Invalid credentials
- SQL query errors
- AI response generation
- Missing required fields

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
