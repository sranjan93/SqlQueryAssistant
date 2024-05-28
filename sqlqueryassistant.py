# -*- coding: utf-8 -*-
"""
Created on Tue May 28 19:44:26 2024

@author: Sanijv Ranjan
"""

import azure.functions as func
import openai
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Extracting user input from the HTTP request
    try:
        req_body = req.get_json()
        prompt = req_body['prompt']
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)
    except KeyError:
        return func.HttpResponse("Missing 'prompt' in request body", status_code=400)

    # Set up OpenAI environment
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Define the system prefix template
    system_prefix_template = """
    You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
    Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.
    You have access to tools for interacting with the database.
    Only use the given tools. Only use the information returned by the tools to construct your final answer.
    You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
    {additional_info}

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP, CREATE etc.) to the database.

    If the question does not seem related to the database, just return "I don't know" as the answer.
    """

    # Define the additional information for each table
    additional_info_mapping = {
        "COMPANY": "company_id, company_name, company_website, company_address_information (city, state, zip, country), company_about, company_products_list",
    }

    # Define the final prompt template
    system_prefix = system_prefix_template.format(dialect='SQL', top_k='10', additional_info="Give preference to the following tables: " + ", ".join(additional_info_mapping.keys()))

    # Construct the final prompt with the updated additional information
    final_prompt = f"{system_prefix}\n\n{prompt}"

    try:
        # Generate SQL query using OpenAI
        response = openai.Completion.create(
            engine="davinci-codex",  # Choose the model engine
            prompt=final_prompt,
            max_tokens=60
        )

        # Extract the SQL query from the response
        sql_query = response.choices[0].text.strip()

        # Return the SQL query as JSON response
        return func.HttpResponse(json.dumps({"sql_query": sql_query}), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)
