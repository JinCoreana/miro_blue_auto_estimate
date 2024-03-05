import os
import json
import pandas as pd
from dotenv import load_dotenv
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

            csvData = pd.read_csv('uploaded.csv')
            
            promptInput=request.form['userText']
            contract= "{description: string;\nunits: number;\nunitPrice: { base: number; currency: number };\nnetAmount: { base: number; currency: number };\ntotalAmount: { base: number; currency: number };\ninsight: string;}"
            userPrompt = f"based on the following csv data {csvData} representing all available items. create a new json data according to the following json contract {contract}. For insight, if prompt does not mention period, use 'The price is based on last 30 days invoices' and also include the summary of why this is the outcome. If there is no perfect matched item, leverage the similar string description and include the summary under insight, Based on all above response to {promptInput}"
            print(f"Prompt: {userPrompt}")
            message = [
                {
                    "role": "system",
                    "content": "As an AI bot developed by Sage that outcomes only json objects in an array as string, my primary function is to assist users with generating line items for contracts. I achieve this by utilizing JSON data to provide detailed insights and average prices based on the quantity and description(80% matched string) entered by the user. Upon receiving input from the user, including quantity and description, I leverage the JSON data available to compute average prices and offer comprehensive explanations for each line item generated. These explanations are tailored to provide users with a clear understanding of how the average prices are derived and any relevant contextual information.",
                },            
                {"role": "user", "content": userPrompt},
                {"role": "user", "content": "The used items should have 80percent of similarity to the prompt item description. If there is not matched items, return [ { \"description\": null, \"units\": 5, \"unitPrice\": { \"base\": null, \"currency\": null }, \"netAmount\": { \"base\": null, \"currency\": null }, \"totalAmount\": { \"base\": null, \"currency\": null }, \"insight\": \"Based on last 30 days invoices. There is no price information for <b>prompt item</b>\" } ],"},
                {"role": "user", "content": "Use 'previous invoices' instead of 'dataset'."},
                {"role": "user", "content": "When processing the data, prioritize accuracy and relevance. Ensure that the generated responses adhere to the context provided in the prompt. If a term is ambiguous, interpret it in the most relevant manner based on the available data. Avoid introducing new information unless explicitly requested."},
                {"role": "user", "content": "Interpret '2024-03-01' as a reference to a day if the prompt mentions '1 day' or 'one day'"},
                {"role": "user", "content": "Interpret '2024-03-01'and '2024-03-02' as a reference to a two days if the prompt mentions '2 days' or 'two days'"},
                {"role": "user", "content": "Verify the accuracy of netAmount and totalAmount without explicitly mentioning them in the response."},
                {"role": "user", "content": "If the CSV data's 'Description' doesn't include the prompt's item name or a related keyword, just return null for all. Utilise similar items enclosed within <b></b> for additional context. Also, provide the average unit price, along with the minimum and maximum unit prices in the format avg: £2099 (min: £2099, max: £2099)."},
                {"role": "user", "content": "Return only JSON-formatted data as a string, excluding ```json and ```, and enclose the entire response within square brackets [] at the beginning and end."},
                   
          ]
            response  = client.chat.completions.create(
                model="gpt-35-turbo-1106",
                messages = message,
                temperature=0.2,
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