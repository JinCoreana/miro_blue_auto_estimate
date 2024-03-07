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
    
@app.route("/estimate", methods=["GET","POST","PUT"])
def estimate():
    if request.method == "GET":
        return render_template("testTemplate.html")
    elif request.method == "POST":
        try:
            requestBody = request.get_json()
            csvData = pd.DataFrame.from_dict(requestBody.get("data"))
            print("requestBody", csvData)
            promptInput = requestBody.get('userText')
        
            contract= "{description: string;\nunits: number;\nunitPrice: { base: number; currency: number };\nnetAmount: { base: number; currency: number };\ntotalAmount: { base: number; currency: number };\ninsight: string;}"
            userPrompt = f"using csv dataset {csvData}. create a new json data according to the following json contract {contract}. For insight, explain how the price is generated info for users to understand including avg: £number (min: £number, max: £number). Make sure to whether it's from our past invoices or general UK market data(if items mentioned in {promptInput} has 90% similarity with any of 'description' in csv data, use the matched description from CSV data for the JSON response. If there are not matching items in csv data, use user´s input and find the market price without mentioning 'Sorry, we could not find the item from your invoice history. But here is the average price in the market.' and which year of the data and 'retrieved from UK market data from 20XX'). Based on all above create outcome from: {promptInput}"
            print(f"Prompt: {userPrompt}")
            message = [
                {
                    "role": "system",
                    "content": "As an AI bot developed by Sage that outcomes only json objects in an array as string, my primary function is to assist users with generating line items, firstly based on {csvData} and secondly UK Market data according to contracts. I outcome JSON data to provide detailed insight and average prices of all invoice objects based on the quantity and description entered in {promptInput}. Upon receiving {promptInput}, including quantity and description, I leverage the JSON data available to compute average prices and offer comprehensive explanations for each line item generated. These explanations are tailored to provide users with a clear understanding of what items were caught from the json dataset, if the similar item could not be found from the csv {csvData} then use UK market data.Return only JSON-formatted data as a string, excluding ```json and ```, and enclose the entire response within square brackets [] at the beginning and end.",
                },            
                { "role": "user", "content": userPrompt },
          ]
            response = client.chat.completions.create(
                model="gpt-35-turbo-1106",
                messages = message,
                temperature=0.2,
                max_tokens=3000,
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
    elif request.method == "PUT":
        try:
            requestBody = request.get_json()
            csvData = pd.DataFrame.from_dict(requestBody.get("data"))
            print("requestBody", csvData)
            previousJson = requestBody.get('previousEstimate')
            insight = requestBody.get('insight')
            userText = requestBody.get('userText')
            
            prompt = f"Using the original JSON data {previousJson} as the template, depending on Insight:{insight} and uesrText:{userText}, revise the JSON data. If you need to add more items, use this csv dataset {csvData} to retrieve the average price and to apply discount, update unit price of the related item not affecting units and unrelated items, don't touch original object whose description was not mentioned in the user input. Return only JSON-formatted data without any other words as a string, excluding ```json and ```, and enclose the entire response within square brackets [] at the beginning and end. Make sure you revise the original JSON data with the new line items added or discounted applied on the exiting JSON object unit price depending on the user input. For insight, if you are updating unit price, remove original string and enter new input how the new price is calculated compared to the original data. Make sure you don't duplicate the same description."
            # Generate new completion text based on updated prompt
            
            print(f"Prompt: {previousJson}, {insight},{userText}")
            message = [  
                 {
                    "role": "system",
                    "content": "As an AI bot developed by Sage that outcomes only json objects in an array as string, using the original JSON contract provided and updated JSON combining text inputs. my primary function is to assist users with generating line items, firstly based on {csvData} and secondly UK Market data according to contracts. I outcome JSON data to provide detailed insight and average prices of all invoice objects based on the quantity and description entered in {promptInput}. Upon receiving {promptInput}, including quantity and description, I leverage the JSON data available to compute average prices and offer comprehensive explanations for each line item generated. These explanations are tailored to provide users with a clear understanding of what items were caught from the json dataset, if the similar item could not be found from the csv {csvData} then use UK market data."
                },
                  {
                    "role": "user",
                    "content": "don't touch the objects in the original Json if the description is not mentioned in the Insight text. If the description is mentioned in the Insight's description, update the unit price of the related item not affecting units and unrelated items, don't touch original object whose description was not mentioned in the user input. If you need to add more items, use this csv dataset {csvData} to retrieve the average price and to apply discount, update unit price of the related item not affecting units and unrelated items, don't touch original object whose description was not mentioned in the user input. Return only JSON-formatted data as a string, excluding ```json and ```, and enclose the entire response within square brackets [] at the beginning and end. Make sure you revise the original JSON data with the new line items added or discounted applied on the exiting JSON object unit price depending on the user input. For insight, if you are updating unit price, remove original string and enter new input how the new price is calculated compared to the original data. Make sure you don't duplicate the same description."
                },
                # {
                #     "role": "user",
                #     "content": "updated this json data [{\"description\":\"Website Design\",\"insight\":\"The price is based on last 30 days invoices. The average price for 'Website Design' based on past invoices is £925 (min: £650, max: £1200).\",\"netAmount\":{\"base\":1200,\"currency\":1200},\"totalAmount\":{\"base\":1200,\"currency\":1200},\"unitPrice\":{\"base\":120,\"currency\":120},\"units\":10},{\"description\":\"Web Hosting\",\"insight\":\"Sorry, we could not find the item from your invoice history. But here is the average price in the market. The average price for 'Web Hosting' retrieved from UK market data from 2023 is £150 per year.\",\"netAmount\":{\"base\":450,\"currency\":450},\"totalAmount\":{\"base\":450,\"currency\":450},\"unitPrice\":{\"base\":150,\"currency\":150},\"units\":3}] leveraging 'Based on your past invoices, you could provide 10 percent discount on 'Hosting' item for minimum 3 years purchase, why don’t you propose it?!'"
                # },
                # {
                #     "role": "assistant",
                #     "content": "replace"  },
                # {
                #     "role": "user",
                #     "content": "updated this json data [{\"description\":\"Website Design\",\"insight\":\"The price is based on last 30 days invoices. The average price for 'Website Design' based on past invoices is £925 (min: £650, max: £1200).\",\"netAmount\":{\"base\":1200,\"currency\":1200},\"totalAmount\":{\"base\":1200,\"currency\":1200},\"unitPrice\":{\"base\":120,\"currency\":120},\"units\":10},{\"description\":\"Web Hosting\",\"insight\":\"Sorry, we could not find the item from your invoice history. But here is the average price in the market. The average price for 'Web Hosting' retrieved from UK market data from 2023 is £150 per year.\",\"netAmount\":{\"base\":450,\"currency\":450},\"totalAmount\":{\"base\":450,\"currency\":450},\"unitPrice\":{\"base\":150,\"currency\":150},\"units\":3}] leveraging 'You could propose 'Logo Design' along with 'Website Design' item, would you like to add it?'"
                # },
                # {
                #     "role": "assistant",
                #     "content": "replace" },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            # gpt-4-1106-preview
            # gpt-35-turbo-1106
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=message,
                temperature=0.2,
                max_tokens=3000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            
            completion_text = response.choices[0].message.content  
            print(f"Azure Response completion_text: {completion_text}")
            
            # Return refined completion_text
            return json.loads(completion_text), 200
            
        except Exception as e:
            print("An error occurred:", e)
            return "An error occurred", 500     
if __name__ == "__main__":
    port = 8081
app.run(port=port)