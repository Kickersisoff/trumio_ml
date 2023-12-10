from django.shortcuts import render
import tempfile
import pymongo
import requests
import pandas as pd
from bson.objectid import ObjectId
import os
import numpy as np

# Create your views here.
# myapi/views.py
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from .serializers import SkillsSerializer
from pyresparser import ResumeParser
from reportlab.pdfgen import canvas

def create_pdf_from_text(text):
    pdf_buffer = BytesIO()

    pdf_canvas = canvas.Canvas(pdf_buffer)


    pdf_canvas.setFont("Helvetica", 12)


    pdf_canvas.drawString(100, 700, text)


    pdf_canvas.save()

    pdf_buffer.seek(0)

    return pdf_buffer

def update_comp_skills():

    df = pd.read_csv("skills.csv")

    mongo_uri = "mongodb+srv://trumio:trumio123@cluster0.vxrqj8f.mongodb.net/?retryWrites=true&w=majority"
    client = pymongo.MongoClient(mongo_uri)
    database = client["trumio"]
    collection = database["projects"]

    projects = [(projects["description"]+" "+" ".join(projects["skills"]),str(projects["_id"])) for projects in collection.find()]

    # print("---\n\n\n",projects)

    lowercase_list = [(string[0].lower(),string[1]) for string in projects]

    # print("\n\n--",lowercase_list)

    for a in lowercase_list:
        # print(a)
    
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name

            pdf_buffer = create_pdf_from_text(a[0])
            temp_file.write(pdf_buffer.read())
        
        data = ResumeParser(temp_path).get_extracted_data()

        temp_file.close()

        # Delete the temporary file from the file system
        os.remove(temp_path)

        skills = data["skills"]
        skills = [a.lower() for a in skills]
        print("--\n\n",skills)

        # os.remove(os.path.join(temp_path, now+".zip"))

        row_name = a[1]
        # print("\n\n---",type(row_name))

        df.loc[str(row_name)] = 0 # Initialize the new row with zeros

        for x in df.columns:
            if x in skills:
                df.loc[str(row_name),x] = 1

    
    df.to_csv("skills.csv")
    # print(df.head())


def user_skill(id):
    df1 = pd.read_csv("skills_user.csv")

    mongo_uri = "mongodb+srv://trumio:trumio123@cluster0.vxrqj8f.mongodb.net/?retryWrites=true&w=majority"
    client = pymongo.MongoClient(mongo_uri)
    database = client["trumio"]
    collection = database["students"]

    objInstance = ObjectId(id)
 
    student = collection.find_one({"_id": objInstance})
    resume = student["resume"]

    # print("\n\n\nResumeee-----",resume)

    try:
        response = requests.get(resume)
        response.raise_for_status()
        pdf_content = response.content
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Error downloading PDF: {str(e)}'}, status=500)

    # Save the PDF content to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(pdf_content)

    data = ResumeParser(temp_path).get_extracted_data()

    temp_file.close()

        # Delete the temporary file from the file system
    os.remove(temp_path)

    skills = data["skills"]
    skills = [a.lower() for a in skills]

    # print("\n\n\n",skills)

    row_name = id
    # print("--- \n\n",type(row_name))

    df1.loc[str(row_name)] = 0 # Initialize the new row with zeros

    for x in df1.columns:
        if x in skills:
            df1.loc[str(row_name),x] = 1

    df1.to_csv("skills_user.csv")
    # print(df.head())


@api_view(['GET'])
@require_GET
def calculate_skills(request):

    query_param = request.query_params.get('my_query_param', None)

    if query_param is None:
        return JsonResponse({'error': 'Missing query parameter'}, status=400)
    
    update_comp_skills()

    user_skill(query_param)

    def count_common_skills(user_row, company_row):
        return sum(x == y == 1 for x, y in zip(user_row, company_row))

    df_user = pd.read_csv("skills_user.csv")
    
    df_user.set_index('Unnamed: 0', inplace=True)
    df = pd.read_csv("skills.csv")
    df.set_index('Unnamed: 0', inplace=True)

    # print("\n\n\n---",df)
    # print("\n\n\n---",df_user)
    # Create a new DataFrame to store the common skills
    common_skills_df = pd.DataFrame(index=df_user.index, columns=df.index)

    for user_index, user_row in df_user.iterrows():
        for company_index, company_row in df.iterrows():
            common_skills_df.loc[user_index, company_index] = count_common_skills(user_row, company_row)

    # print("\n\n----",common_skills_df.head())
    common_skills_df.to_csv("new.csv")
    final_df = pd.read_csv("new.csv")
    # common_skills_df["Unnamed: 0"] = 0
    final_df.set_index("Unnamed: 0",inplace=True)

    target_row = final_df.loc[final_df.index[0]]
    # print(target_row.items)

    # Create a tuple of column-value pairs for the specified row
    column_value_pairs = list(target_row.items())

    # final = sorted(column_value_pairs,key = lambda x:x[1],reverse=True)

    

    serializer = SkillsSerializer({'skills': column_value_pairs})

    return JsonResponse(serializer.data)
