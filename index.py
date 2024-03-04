import json
import http.client
from flask import Flask, request
from flask_cors import CORS
import requests
import openai
import json
import re

openai.api_type = "azure"
openai.api_base = "https://da-stg-openai-eu-fr-m6allrbs2iz3e.openai.azure.com/"
openai.api_version = "2023-03-15-preview"
openai.api_key = "AZURE_OPENAI_KEY"
model = "gpt-4"
# model = "gpt-35-turbo"
app = Flask(__name__)
CORS(app)
def download_file(url):
    response = requests.get(url, allow_redirects=True, verify=False)
    if response.status_code == 200:
        return response.content.decode("utf-8")
    else:
        print(f"Failed to download the file from {url}")
def count_tokens(input_text, input_model):
    token_count = len(input_text.split())
    print("Token count:", token_count)
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        csvUrl = data["csvUrl"]
        reportType = data["reportType"]
        summaryType = data["summaryType"]
        print(f"Report Type: {reportType}")
        csvData = download_file(csvUrl)
        csv_without_quotes = csvData.replace('"', "")
        if reportType == "ProfitAndLoss":
            reportTypeString = "Profit And Loss"
        elif reportType == "BalanceSheet":
            reportTypeString = "Balance Sheet"
        if summaryType == "summary":
            summaryPrompt = "analyze the following csv data and provide a summary of less than 100 words on how my business is doing"
            maxTokens = 150
        elif summaryType == "insights":
            summaryPrompt = "analyze the following csv data and provide 3 bullet points with main highlights summary on how my business is doing and 2 recommendations to improve my business"
            maxTokens = 250
        userPrompt = f"based on the following csv data representing a {reportTypeString} financial report. {summaryPrompt}: {csv_without_quotes}"
        print(f"Prompt: {userPrompt}")
        message = [
            {
                "role": "system",
                "content": "You are an AI trained to provide financial analysis based on financial statements.",
            },
            {"role": "user", "content": userPrompt},
        ]
        # count_tokens(userPrompt, model)
        # connection = http.client.HTTPSConnection(OPENAI_API_URL)# connection.request("POST", "/v1/engines/davinci/completions", body = payload_str, headers = headers)# response = connection.getresponse()
        response = openai.ChatCompletion.create(
            engine=model,
            messages=message,
            temperature=0.5,
            max_tokens=maxTokens,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )
        # response_data = response.read().decode('utf-8')
        print(f"Azure Response: {response}")
        completion_text = response["choices"][0]["message"]
        print(f"Azure Response completion_text: {completion_text}")
        return completion_text, "200"
    except openai.error.APIError as e:
        # Handle API error here, e.g. retry or log
        errMessage = f"OpenAI API returned an API Error: {e}"
        print(errMessage)
        return errMessage, 500
        pass
    except openai.error.APIConnectionError as e:
        # Handle connection error here
        errMessage = f"OpenAI API returned an API Error: {e}"
        print(errMessage)
        return errMessage, 500
        pass
    except openai.error.RateLimitError as e:
        # Handle rate limit error (we recommend using exponential backoff)
        errMessage = f"OpenAI API returned an API Error: {e}"
        print(errMessage)
        return errMessage, 500
        pass
    except Exception as e:
        print("An error occurred:", e)
        return "An error occurred", 500
if __name__ == "__main__":
    port = 8081
app.run(port=port)