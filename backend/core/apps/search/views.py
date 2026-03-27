from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
import json
from apps.analysis import ai_search
from apps.dataset import data_eda

def search(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    if request.body:
        data = json.load(request.body)
    else:
        data = {}
    
    category = data.get("category")
    s_query = data.get("query")
    task = data.get("task")
    data_age = data.get("age")
    desc = data.get("description")
    data_sources = data.get("preferred_sources")

