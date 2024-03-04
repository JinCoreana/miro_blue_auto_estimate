from dotenv import load_dotenv
import os
import json
from openai import AzureOpenAI
from flask import Flask, request, render_template
from flask_cors import CORS

load_dotenv()

client = AzureOpenAI(
  azure_endpoint = "https://sagehackathonai.openai.azure.com/", 
  api_key=os.getenv("AZURE_OPENAI_KEY"),  
  api_version="2024-02-15-preview"
)

app = Flask(__name__)
CORS(app)

# def count_tokens(input_text, input_model):
#     token_count = len(input_text.split())
#     print("Token count:", token_count)
    
@app.route("/estimate", methods=["GET","POST"])
def estimate():
    if request.method == "GET":
        return render_template("testTemplate.html")
    elif request.method == "POST":
        try:
            if 'csvFile' not in request.files:
                return 'No file part'
            
            csv_file = request.files['csvFile']
            
            if csv_file.filename == '':
                return 'No selected file'
            
            csv_file.save('uploaded.csv')

            import pandas as pd
            csvData = pd.read_csv('uploaded.csv')
            
            client = AzureOpenAI(
                azure_endpoint="https://sagehackathonai.openai.azure.com/",
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-02-15-preview"
            )
            promptInput=request.form['userText']
            contract= "{order: number;\ndescription: string;\nunits: number;\nunitPrice: { base: number; currency: number };\nnetAmount: { base: number; currency: number };\ntotalAmount: { base: number; currency: number };\ninsight: string;}"
            userPrompt = f"based on the following csv data {csvData} representing all available items. create a new json data according to the following json contract {contract}. For insight, if prompt does not mention period, use 'The above data is based on last 30 days data' and also include the summary of why this is the outcome. If there is no perfect matched item, leverage the similar items and include the summary under insight, Based on all above response to {promptInput}"
            print(f"Prompt: {userPrompt}")
            message = [
                {
                    "role": "system",
                    "content": "You are an AI bot for Sage.Ltd. You are trained to provide line items for a given contract. According to quantity and description that user entered and leverage all json data and provide average prices with explanation.",
                },
                {"role": "user", "content": userPrompt},
                {"role": "user", "content": "Only return json format data without any other words and exclude ```json and ``` at the beginning and end of the response."},
                      ]
            response  = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages = message,
                temperature=0.7,
                max_tokens=800,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            completion_text = response.choices[0].message.content  
            print(f"Azure Response completion_text: {completion_text}")
            return json.loads(completion_text), "200"
   
        except Exception as e:
            print("An error occurred:", e)
            return "An error occurred", 500
        
if __name__ == "__main__":
    port = 8081
app.run(port=port)