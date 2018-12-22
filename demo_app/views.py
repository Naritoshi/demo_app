from django.shortcuts import render, redirect
from django.db import connection
from .forms import InputForm
from .models import Customers
from sklearn.externals import joblib
import numpy as np

loaded_model = joblib.load('demo_app/demo_model.pkl')
print("[Trained Model] loaded.")

# Create your views here.
def index(request):
    return render(request, 'demo_app/index.html', {})

def input_form(request):
    if request.method == 'POST':
        form = InputForm(request.POST)
        if form.is_valid():
            form.save()#入力した値を保存
            return redirect('result')
        else:
            return redirect(form.errors)
    else:
        form = InputForm()
        return render(request, 'demo_app/input_form.html', {'form':form})

def result(request):
    customers = Customers.objects.order_by('id').reverse().values_list\
    ('limit_balance', 'sex', 'education', 'marriage', 'age', 'pay_0', 'pay_2','pay_3',\
     'pay_4', 'pay_5', 'pay_6', 'bill_amt_1', 'pay_amt_1', 'pay_amt_2','pay_amt_3', 'pay_amt_4', 'pay_amt_5', 'pay_amt_6')

    x = np.array([customers[0]])
    print(x)

    y = loaded_model.predict(x)[0]
    y_proba = loaded_model.predict_proba(x)[0][y]
    y_proba = round(y_proba * 100, 2)
    result = (y, y_proba)
    print(result)

    print(connection.queries[-1]['sql'])

    if y == 0:
        if y_proba >= 75:
            comment = '貸しても返ってこない'
        else:
            comment = '貸しても返ってこないかも'
    else:
        if y_proba >= 75:
            comment = '貸していい'
        else:
            comment = '貸してもいい'
    
    #推論結果の保存
    customer = Customers.objects.order_by('id').reverse()[0]
    customer.result = y
    customer.proba = y_proba
    customer.comment = comment
    customer.save()

    return  render(request, 'demo_app/result.html', {'y':y, 'y_proba': y_proba, 'comment':comment})

def history(request):
    if request.method == 'POST':
        d_id = request.POST
        d_customer = Customers.objects.filter(id=d_id['d_id'])
        d_customer.delete()

    customers = Customers.objects.all()
    return render(request, 'demo_app/history.html', {'customers':customers})

def calicurate(request):
    calc_result = ''
    if request.method == 'POST':
        nums = request.POST
        num1 = nums['num1']
        num2 = nums['num2']
        if (num1.isdigit() and num2.isdigit()):
            calc_result = int(num1) + int(num2)
        
    return  render(request, 'demo_app/calicurate.html', {'answer':calc_result})