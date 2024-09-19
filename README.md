# SQL_Talk

![Logo](https://images.datacamp.com/image/upload/v1649063788/image5_mokwti.png)

## SQL_Talk is a Python project that connects to a SQL Server database and the OpenAI API. It aims to identify the complete structure of the data model and allow users to ask questions in natural language. SQL_Talk converts these questions into SQL queries and provides accurate answers in natural language as well.

## Features

- **Installing resources and libraries:** Installs the docxtpl and python-docx libraries required to work with Word document templates.
- **Setting Up SQL Server Connection:** We configure the connection string to connect to the SQL Server database using SQLAlchemy and pyodbc.
- **Creating the SQLDatabase Instance:** We use langchain to create an instance of SQLDatabase that will connect to our database.
- **Importing APIs and Configuring the Language Model (LLM):** We set the OpenAI API key in the environment variables and configure the OpenAI language model.
- **Creating the SQL Database String:** We create a SQL database chain using SQLDatabaseChain from langchain_experimental
- **Query Function Definition and Usage Example:** We define a function that formats the user's query and uses the SQL database string to retrieve the results. We provide an example of using the query function to verify its operation.
- **Streamlit Initial Setup:** We set up the basic structure of the application in Streamlit, including the title and input fields for the OpenAI API, the SQL server name, and the database name.
- **Connecting to the Database:** We configure the connection string to SQL Server and create the engine using SQLAlchemy.
- **Setting Up the Model (LLM) and Creating the SQL Database Chain:** We set up the OpenAI language model and created the SQL database chain using SQLDatabaseChain.
- **Query Function:** We define the query function that formats the user query and retrieves the results using the SQL database string.
- **User Interface for Making Queries:** We built the user interface in Streamlit so that users can enter their SQL queries and see the results.

## Technologies used

- **Streamlit:** Streamlit is an open-source app framework used to create and share beautiful, custom web apps for machine learning and data science. It allows you to turn data scripts into shareable web apps in minutes.
- **OS (Operating System):** The os module in Python provides a way of using operating system-dependent functionality like reading or writing to the file system. It is used here to set environment variables.
- **SQLAlchemy:** SQLAlchemy is a SQL toolkit and Object-Relational Mapping (ORM) library for Python. It provides a full suite of well-known enterprise-level persistence patterns, designed for efficient and high-performing database access.
- **pyodbc:** pyodbc is an open-source Python module that makes accessing ODBC databases simple. It allows you to connect to databases using ODBC drivers.
- **LangChain:** LangChain is a framework for developing applications powered by language models. It provides tools to connect language models to other data sources and APIs, enabling complex workflows.
- **OpenAI API:** The OpenAI API provides access to OpenAI’s powerful language models, such as GPT-3.5. It allows developers to integrate advanced natural language processing capabilities into their applications.
- **SQLDatabase:** Part of the LangChain library, SQLDatabase is a module that facilitates interaction with SQL databases. It abstracts the complexities of database connections and queries.
- **ChatOpenAI:** ChatOpenAI is a module from LangChain that allows interaction with OpenAI’s chat models. It is used to generate responses based on user input.
- **SQLDatabaseChain:** SQLDatabaseChain is an experimental module from LangChain that combines language models with SQL databases. It enables the creation of complex query workflows that leverage both natural language processing and database operations.

## **Documentation**
! https://fcernafukuzaki.medium.com/ms-sql-server-2019-gpt-langchain-b0d83e6a369e
! https://www.youtube.com/watch?v=yz1CaFMTevk&t=478s
! https://www.youtube.com/watch?v=vvLzNEiBkIM&t=199s
