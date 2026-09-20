-- Initial database script for Data Agent

-- 1. Create Domain Tables for SQL Analyst Agent queries
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    location VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    salary NUMERIC(10, 2) NOT NULL,
    hire_date DATE NOT NULL,
    department_id INT REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(employee_id),
    amount NUMERIC(12, 2) NOT NULL,
    sale_date DATE NOT NULL,
    region VARCHAR(50)
);

-- Insert sample seed data
INSERT INTO departments (department_name, location) VALUES
('Engineering', 'New York'),
('Sales', 'San Francisco'),
('Marketing', 'Chicago'),
('HR', 'New York')
ON CONFLICT DO NOTHING;

INSERT INTO employees (first_name, last_name, email, salary, hire_date, department_id) VALUES
('Alice', 'Smith', 'alice@example.com', 95000.00, '2021-03-15', 1),
('Bob', 'Jones', 'bob@example.com', 75000.00, '2022-06-01', 2),
('Charlie', 'Brown', 'charlie@example.com', 82000.00, '2020-01-10', 2),
('Diana', 'Prince', 'diana@example.com', 110000.00, '2019-11-20', 1),
('Evan', 'Wright', 'evan@example.com', 68000.00, '2023-02-14', 3)
ON CONFLICT (email) DO NOTHING;

INSERT INTO sales (employee_id, amount, sale_date, region) VALUES
(2, 15000.00, '2024-01-15', 'West'),
(2, 22000.00, '2024-02-10', 'West'),
(3, 18000.00, '2024-01-20', 'East'),
(3, 30000.00, '2024-03-05', 'East'),
(2, 12000.00, '2024-03-12', 'West')
ON CONFLICT DO NOTHING;

-- 2. Create Agent Execution Log Table (matching AgentSchema)
CREATE TABLE IF NOT EXISTS agent_execution_logs (
    id SERIAL PRIMARY KEY,
    curated_ques TEXT,
    prompt_query_text TEXT,
    is_safe VARCHAR(5),
    generated_sql_query TEXT,
    sql_query_execution_result TEXT,
    final_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
